from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import typer

from app.config import get_settings
from app.domain.enums import ReviewStatus, UgandaRelation
from app.domain.schemas import DiscoveryQuery
from app.ingestion.candidates import (
    approve_candidate,
    list_review_queue,
    persist_candidate_proposals,
    reject_candidate,
)
from app.intelligence.gemini import GeminiIntelligenceProvider
from app.operations import (
    derive_quarter,
    eligible_github_entity_ids,
    ingest_github_batch,
    ingest_github_entity,
    publish_quarter,
    validate_quarter,
)

app = typer.Typer(
    name="toptenug",
    help="TopTenUG ingestion and quarterly ranking operations.",
    no_args_is_help=True,
)
ingest_app = typer.Typer(help="Collect hard metrics from authoritative source APIs.")
review_app = typer.Typer(help="Review grounded candidate records before ranking eligibility.")
app.add_typer(ingest_app, name="ingest")
app.add_typer(review_app, name="review")


@dataclass
class JobRecord:
    id: str
    job_type: str
    status: str
    started_at: str
    finished_at: str | None
    counts: dict[str, int]
    failure_details: dict[str, str] | None
    parameters: dict[str, str]


class JobRecorder:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(".toptenug/jobs.jsonl")

    def append(self, record: JobRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    @contextmanager
    def track(self, job_type: str, **params: str) -> Iterator[dict[str, int]]:
        start = datetime.now(UTC)
        job_id = str(uuid4())
        counts: dict[str, int] = {}
        try:
            yield counts
        except Exception as exc:
            self.append(
                JobRecord(
                    job_id,
                    job_type,
                    "FAILED",
                    start.isoformat(),
                    datetime.now(UTC).isoformat(),
                    counts,
                    {"type": type(exc).__name__, "message": str(exc)},
                    params,
                )
            )
            raise
        else:
            self.append(
                JobRecord(
                    job_id,
                    job_type,
                    "SUCCEEDED",
                    start.isoformat(),
                    datetime.now(UTC).isoformat(),
                    counts,
                    None,
                    params,
                )
            )


def _session_local() -> Any:
    from app.db import SessionLocal

    return SessionLocal


def _dump(value: Any) -> None:
    typer.echo(json.dumps(value, indent=2, default=str, sort_keys=True))


def _validate_quarter(value: str) -> None:
    if not (
        len(value) == 7
        and value[4:6] == "-Q"
        and value[:4].isdigit()
        and value[6] in "1234"
    ):
        raise typer.BadParameter("quarter must use YYYY-QN where N is 1..4")


@app.command()
def discover(
    universe: str = typer.Option(..., "--universe"),
    persist: bool = typer.Option(False, "--persist"),
) -> None:
    settings = get_settings()
    with JobRecorder().track("discover", universe=universe, persist=str(persist)) as counts:
        proposals = GeminiIntelligenceProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        ).discover(DiscoveryQuery(text=f"Ugandan {universe} builders and public evidence"))
        counts["proposals"] = len(proposals)

        if not persist:
            _dump([proposal.model_dump(mode="json") for proposal in proposals])
            return

        with _session_local()() as session:
            summary = persist_candidate_proposals(session, proposals, "gemini-search")
        counts["created"] = summary.created
        counts["updated"] = summary.updated
        counts["review_required"] = summary.review_required
        _dump(
            {
                "proposals": summary.proposals,
                "created": summary.created,
                "updated": summary.updated,
                "review_required": summary.review_required,
            }
        )


@review_app.command("list")
def review_list(
    status: ReviewStatus = typer.Option(ReviewStatus.REVIEW_REQUIRED, "--status"),
) -> None:
    with _session_local()() as session:
        rows = list_review_queue(session, status)
        _dump(
            [
                {
                    "id": str(row.id),
                    "display_name": row.display_name,
                    "github_login": row.github_login,
                    "review_status": row.review_status.value,
                    "confidence": row.confidence,
                    "source_count": len(row.source_urls),
                }
                for row in rows
            ]
        )


@review_app.command("approve")
def review_approve(
    candidate: UUID = typer.Option(..., "--candidate"),
    relation: UgandaRelation = typer.Option(..., "--relation"),
    note: str = typer.Option(..., "--note"),
) -> None:
    with _session_local()() as session:
        entity = approve_candidate(session, candidate, relation, note)
        _dump(
            {
                "candidate_id": str(candidate),
                "entity_id": str(entity.id),
                "review_status": entity.review_status.value,
                "uganda_relation": entity.uganda_relation.value if entity.uganda_relation else None,
                "eligible": entity.is_eligible,
            }
        )


@review_app.command("reject")
def review_reject(
    candidate: UUID = typer.Option(..., "--candidate"),
    note: str = typer.Option(..., "--note"),
) -> None:
    with _session_local()() as session:
        row = reject_candidate(session, candidate, note)
        _dump(
            {
                "candidate_id": str(row.id),
                "review_status": row.review_status.value,
            }
        )


@ingest_app.command("github")
def ingest_github(entity: UUID = typer.Option(..., "--entity")) -> None:
    with JobRecorder().track("ingest-github", entity=str(entity)) as counts:
        with _session_local()() as session:
            inserted = asyncio.run(ingest_github_entity(session, entity))
        counts["observations"] = inserted
        _dump({"entity": str(entity), "observations_added": inserted})


@ingest_app.command("github-batch")
def ingest_github_batch_command(
    limit: int = typer.Option(25, "--limit", min=1, max=500),
    entity_file: Path | None = typer.Option(None, "--entity-file", exists=True, dir_okay=False),
) -> None:
    with JobRecorder().track(
        "ingest-github-batch",
        limit=str(limit),
        entity_file=str(entity_file) if entity_file else "",
    ) as counts:
        with _session_local()() as session:
            if entity_file is None:
                entity_ids = eligible_github_entity_ids(session, limit=limit)
            else:
                entity_ids = [
                    UUID(line.strip())
                    for line in entity_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            result = asyncio.run(
                ingest_github_batch(session, entity_ids, continue_on_error=True)
            )
        counts["attempted"] = result.attempted
        counts["succeeded"] = result.succeeded
        counts["failed"] = result.failed
        counts["observations_added"] = result.observations_added
        _dump(
            {
                "run_id": str(result.run_id),
                "attempted": result.attempted,
                "succeeded": result.succeeded,
                "failed": result.failed,
                "observations_added": result.observations_added,
                "failures": [failure.as_dict() for failure in result.failures],
            }
        )


@app.command()
def derive(quarter: str = typer.Option(..., "--quarter")) -> None:
    _validate_quarter(quarter)
    with JobRecorder().track("derive", quarter=quarter) as counts:
        with _session_local()() as session:
            derived = derive_quarter(session, quarter)
        counts["derived_metrics"] = derived
        _dump({"quarter": quarter, "derived_metrics": derived})


@app.command()
def validate(
    category: str = typer.Option(..., "--category"),
    quarter: str = typer.Option(..., "--quarter"),
) -> None:
    _validate_quarter(quarter)
    with JobRecorder().track("validate", category=category, quarter=quarter) as counts:
        with _session_local()() as session:
            report = validate_quarter(session, category, quarter)
        counts["errors"] = len(report.errors)
        counts["blocking_anomalies"] = len(report.blocking_anomalies)
        _dump(
            {
                "ok": report.ok,
                "errors": report.errors,
                "blocking_anomalies": report.blocking_anomalies,
            }
        )
        if not report.ok:
            raise typer.Exit(2)


@app.command()
def publish(
    category: str = typer.Option(..., "--category"),
    quarter: str = typer.Option(..., "--quarter"),
) -> None:
    _validate_quarter(quarter)
    with JobRecorder().track("publish", category=category, quarter=quarter) as counts:
        with _session_local()() as session:
            run = publish_quarter(session, category, quarter)
        counts["published_runs"] = 1
        _dump({"run_id": str(run.id), "status": run.status, "quarter": run.quarter})


def main() -> None:
    app()


if __name__ == "__main__":
    main()
