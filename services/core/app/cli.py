from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from app.api.store import PublicRankingResult, PublicRankingRun, public_store
from app.domain.enums import RankingRunStatus, RankingType
from app.domain.schemas import ObservationInput
from app.ingestion.pipeline import InMemoryObservationStore
from app.intelligence.base import CandidateProposal
from app.quarterly.publish import Quarter, QuarterPublisher
from app.quarterly.validate import ValidationCandidate
from app.ranking.engine import CandidateMetrics, RankingEngine
from app.ranking.loader import load_algorithm_spec

DEV_RANK_SPEC = Path(__file__).resolve().parents[1] / "algorithms" / "devrankug" / "v1.0.0.yaml"
CATEGORY_ID = uuid5(NAMESPACE_URL, "toptenug:ranking:github-developers")


def _parse_quarter(value: str) -> Quarter:
    year_text, quarter_text = value.split("-Q", 1)
    return Quarter(int(year_text), int(quarter_text))


def _quarter_observed_at(quarter: Quarter) -> datetime:
    month = quarter.number * 3
    return datetime(quarter.year, month, 28, 23, 59, 59, tzinfo=UTC)


def _entity_id_for(proposal: CandidateProposal) -> UUID:
    github = proposal.candidate_profiles.get("github")
    stable_identity = f"github:{github.casefold()}" if github else f"candidate:{proposal.display_name.casefold()}"
    return uuid5(NAMESPACE_URL, f"toptenug:{stable_identity}")


def _slug_for(proposal: CandidateProposal) -> str:
    github = proposal.candidate_profiles.get("github")
    if github:
        return github.casefold()
    return "-".join(proposal.display_name.casefold().split())


def run_first_vertical_fixture(
    proposals: list[CandidateProposal],
    metrics_by_github: dict[str, dict[str, float | int]],
    *,
    quarter: str,
) -> PublicRankingRun:
    """Run the first vertical through deterministic ranking and publication boundaries.

    This entry point is deliberately network-free for reproducible fixtures. Live jobs replace the
    supplied discovery/source inputs with Gemini and GitHub adapters; ranking stays identical.
    """
    parsed_quarter = _parse_quarter(quarter)
    observed_at = _quarter_observed_at(parsed_quarter)
    store = InMemoryObservationStore()
    spec = load_algorithm_spec(DEV_RANK_SPEC)

    candidates: list[CandidateMetrics] = []
    proposal_by_id: dict[UUID, CandidateProposal] = {}
    for proposal in proposals:
        github = proposal.candidate_profiles.get("github")
        if not github or github not in metrics_by_github:
            continue
        entity_id = _entity_id_for(proposal)
        proposal_by_id[entity_id] = proposal
        evidence_url = str(proposal.source_urls[0])
        evidence_id = uuid5(NAMESPACE_URL, f"evidence:{evidence_url}")
        observed_metrics: dict[str, float | int | None] = {}
        for metric_key, value in metrics_by_github[github].items():
            observation = ObservationInput(
                metric_key=metric_key,
                raw_value=value,
                observed_at=observed_at,
                source_url=f"https://github.com/{github}",
                evidence_id=evidence_id,
                source_record_id=f"{github}:{metric_key}:{quarter}",
                metadata={"provider": "github", "candidate_source": evidence_url},
            )
            stored = store.add(observation)
            observed_metrics[metric_key] = stored.raw_value if isinstance(stored.raw_value, (int, float)) else None
        candidates.append(CandidateMetrics(entity_id=entity_id, metrics=observed_metrics, eligible=True))

    scored = RankingEngine().run(spec, candidates)
    validator_rows = [
        ValidationCandidate(
            entity_id=row.entity_id,
            score=row.score,
            rank=row.rank,
            factor_coverage=row.factor_coverage,
            provenance_count=len(proposal_by_id[row.entity_id].source_urls),
        )
        for row in scored
        if row.meets_minimum_coverage
    ]
    publisher = QuarterPublisher()
    publisher.set_candidates(validator_rows)
    published = publisher.publish(parsed_quarter, CATEGORY_ID, spec.version)

    public_results: list[PublicRankingResult] = []
    by_entity = {row.entity_id: row for row in scored}
    for validation_row in published.results:
        scored_row = by_entity[validation_row.entity_id]
        proposal = proposal_by_id[validation_row.entity_id]
        result_id = uuid5(NAMESPACE_URL, f"toptenug:{quarter}:github-developers:{validation_row.entity_id}")
        public_results.append(PublicRankingResult(
            id=result_id,
            entity_id=validation_row.entity_id,
            slug=_slug_for(proposal),
            name=proposal.display_name,
            rank=validation_row.rank,
            score=validation_row.score,
            confidence=proposal.confidence,
            factor_breakdown={name: asdict(value) for name, value in scored_row.factor_breakdown.items()},
            evidence_urls=tuple(str(url) for url in proposal.source_urls),
        ))

    public_run = PublicRankingRun(
        id=published.id,
        slug="github-developers",
        quarter=quarter,
        ranking_type=RankingType.INDEX,
        algorithm_name=spec.name,
        algorithm_version=spec.version,
        status=RankingRunStatus.PUBLISHED,
        published_at=published.published_at,
        methodology_url="/v1/methodology/devrankug-v1",
        results=tuple(public_results),
    )
    public_store.add_run(public_run)
    return public_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="toptenug")
    commands = parser.add_subparsers(dest="command", required=True)

    discover = commands.add_parser("discover")
    discover.add_argument("--universe", required=True)

    ingest = commands.add_parser("ingest")
    ingest.add_argument("source", choices=["github"])
    ingest.add_argument("--entity", required=True)

    derive = commands.add_parser("derive")
    derive.add_argument("--quarter", required=True)

    validate = commands.add_parser("validate")
    validate.add_argument("--category", required=True)
    validate.add_argument("--quarter", required=True)

    publish = commands.add_parser("publish")
    publish.add_argument("--category", required=True)
    publish.add_argument("--quarter", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps({"command": args.command, "status": "accepted", **vars(args)}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
