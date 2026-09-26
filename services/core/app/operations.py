from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.enums import EvidenceLevel, RankingRunStatus, RankingType, ReviewStatus
from app.domain.models import (
    AlgorithmDefinition,
    DerivedMetric,
    Entity,
    Evidence,
    IngestionRun,
    Observation,
    RankingCategory,
    RankingResult,
    RankingRun,
    Source,
    SourceAccount,
)
from app.domain.schemas import EntityRef
from app.quarterly.validate import QuarterValidator, ValidationInput, ValidationReport
from app.ranking.engine import CandidateMetrics, RankingEngine, ScoredCandidate
from app.ranking.loader import AlgorithmSpec, load_algorithm_spec
from app.sources.base import RetryableSourceError
from app.sources.github import GitHubAdapter

ROLLUP_VERSION = "observation-rollup-v1"
CATEGORY_ALGORITHMS = {"github-developers": ("DevRankUG", "1.0.0", RankingType.INDEX)}


def _quarter_parts(value: str) -> tuple[int, int]:
    if (
        len(value) != 7
        or value[4:6] != "-Q"
        or not value[:4].isdigit()
        or value[6] not in "1234"
    ):
        raise ValueError("quarter must use YYYY-QN where N is 1..4")
    return int(value[:4]), int(value[6])


def _quarter_end_exclusive(value: str) -> datetime:
    year, quarter = _quarter_parts(value)
    return (
        datetime(year + 1, 1, 1, tzinfo=UTC)
        if quarter == 4
        else datetime(year, quarter * 3 + 1, 1, tzinfo=UTC)
    )


def _previous_quarter(value: str) -> str:
    year, quarter = _quarter_parts(value)
    return f"{year - 1}-Q4" if quarter == 1 else f"{year}-Q{quarter - 1}"


def _algorithm_path(name: str, version: str) -> Path:
    if (name, version) == ("DevRankUG", "1.0.0"):
        return Path(__file__).resolve().parent.parent / "algorithms" / "devrankug" / "v1.0.0.yaml"
    raise ValueError(f"No local algorithm specification registered for {name} {version}")


def ensure_category_and_algorithm(
    session: Session, slug: str
) -> tuple[RankingCategory, AlgorithmDefinition, AlgorithmSpec]:
    try:
        name, version, ranking_type = CATEGORY_ALGORITHMS[slug]
    except KeyError as exc:
        raise ValueError(f"Unsupported ranking category: {slug}") from exc
    spec = load_algorithm_spec(_algorithm_path(name, version))
    category = session.scalar(select(RankingCategory).where(RankingCategory.slug == slug))
    if category is None:
        category = RankingCategory(
            slug=slug,
            name="GitHub Developers",
            ranking_type=ranking_type,
            eligibility_policy=spec.eligibility_policy,
        )
        session.add(category)
        session.flush()
    algorithm = session.scalar(
        select(AlgorithmDefinition).where(
            AlgorithmDefinition.name == name,
            AlgorithmDefinition.version == version,
        )
    )
    if algorithm is None:
        algorithm = AlgorithmDefinition(
            name=name,
            version=version,
            ranking_type=ranking_type,
            spec=spec.model_dump(mode="json"),
        )
        session.add(algorithm)
        session.flush()
    return category, algorithm, spec


def _ensure_github_source(session: Session) -> Source:
    source = session.scalar(select(Source).where(Source.key == "github"))
    if source is None:
        source = Source(
            key="github",
            name="GitHub",
            base_url="https://github.com",
            evidence_level=EvidenceLevel.A,
        )
        session.add(source)
        session.flush()
    return source


def github_login_for_entity(session: Session, entity_id: UUID) -> str:
    source = _ensure_github_source(session)
    account = session.scalar(
        select(SourceAccount).where(
            SourceAccount.entity_id == entity_id,
            SourceAccount.source_id == source.id,
        )
    )
    if account is None:
        raise ValueError(f"Entity {entity_id} has no verified GitHub source account.")
    return account.external_id


async def ingest_github_entity(session: Session, entity_id: UUID) -> int:
    settings = get_settings()
    source = _ensure_github_source(session)
    login = github_login_for_entity(session, entity_id)
    rows = await GitHubAdapter(
        token=settings.github_token,
        api_base_url=settings.github_api_base_url,
    ).collect(EntityRef(id=entity_id, external_id=login))
    inserted = 0
    for row in rows:
        if session.get(Evidence, row.evidence_id) is None:
            session.add(
                Evidence(
                    id=row.evidence_id,
                    entity_id=entity_id,
                    source_id=source.id,
                    level=EvidenceLevel.A,
                    source_url=row.source_url,
                    retrieved_at=datetime.now(UTC),
                    claim=f"GitHub reported {row.metric_key}={row.raw_value}",
                    confidence=1.0,
                )
            )
        record_id = row.source_record_id or str(row.evidence_id)
        existing = session.scalar(
            select(Observation).where(
                Observation.source_id == source.id,
                Observation.source_record_id == record_id,
                Observation.metric_key == row.metric_key,
                Observation.observed_at == row.observed_at,
            )
        )
        if existing:
            continue
        session.add(
            Observation(
                entity_id=entity_id,
                source_id=source.id,
                evidence_id=row.evidence_id,
                source_record_id=record_id,
                metric_key=row.metric_key,
                raw_value=row.raw_value,
                observed_at=row.observed_at,
                retrieved_at=datetime.now(UTC),
                source_url=row.source_url,
            )
        )
        inserted += 1
    session.commit()
    return inserted


@dataclass(frozen=True)
class BatchIngestionFailure:
    entity_id: UUID
    error_type: str
    message: str
    retryable: bool
    retry_after_seconds: int | None = None
    reset_at: datetime | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "entity_id": str(self.entity_id),
            "error_type": self.error_type,
            "message": self.message,
            "retryable": self.retryable,
            "retry_after_seconds": self.retry_after_seconds,
            "reset_at": self.reset_at.isoformat() if self.reset_at else None,
        }


@dataclass(frozen=True)
class BatchIngestionResult:
    run_id: UUID
    attempted: int
    succeeded: int
    failed: int
    observations_added: int
    failures: tuple[BatchIngestionFailure, ...]


def eligible_github_entity_ids(session: Session, *, limit: int = 25) -> list[UUID]:
    source = _ensure_github_source(session)
    return list(
        session.scalars(
            select(Entity.id)
            .join(SourceAccount, SourceAccount.entity_id == Entity.id)
            .where(
                Entity.is_eligible.is_(True),
                Entity.review_status == ReviewStatus.APPROVED,
                SourceAccount.source_id == source.id,
            )
            .order_by(Entity.id)
            .limit(limit)
        ).all()
    )


async def ingest_github_batch(
    session: Session,
    entity_ids: list[UUID],
    *,
    continue_on_error: bool = True,
) -> BatchIngestionResult:
    run = IngestionRun(
        source_key="github",
        status="RUNNING",
        counts={
            "attempted": len(entity_ids),
            "succeeded": 0,
            "failed": 0,
            "observations_added": 0,
        },
    )
    session.add(run)
    session.commit()
    run_id = run.id

    succeeded = 0
    observations_added = 0
    failures: list[BatchIngestionFailure] = []

    for entity_id in entity_ids:
        try:
            observations_added += await ingest_github_entity(session, entity_id)
            succeeded += 1
        except Exception as exc:
            session.rollback()
            if isinstance(exc, RetryableSourceError):
                retryable = True
                retry_after_seconds = exc.retry_after_seconds
                reset_at = exc.reset_at
            else:
                retryable = False
                retry_after_seconds = None
                reset_at = None
            failure = BatchIngestionFailure(
                entity_id=entity_id,
                error_type=type(exc).__name__,
                message=str(exc),
                retryable=retryable,
                retry_after_seconds=retry_after_seconds,
                reset_at=reset_at,
            )
            failures.append(failure)
            if not continue_on_error:
                durable_run = session.get(IngestionRun, run_id)
                if durable_run is not None:
                    durable_run.status = "FAILED"
                    durable_run.finished_at = datetime.now(UTC)
                    durable_run.counts = {
                        "attempted": len(entity_ids),
                        "succeeded": succeeded,
                        "failed": len(failures),
                        "observations_added": observations_added,
                    }
                    durable_run.failure_details = {
                        "failures": [item.as_dict() for item in failures]
                    }
                    session.commit()
                raise

    failed = len(failures)
    durable_run = session.get(IngestionRun, run_id)
    if durable_run is None:
        raise RuntimeError(f"Ingestion run {run_id} disappeared during batch processing")
    durable_run.status = "SUCCEEDED" if failed == 0 else ("FAILED" if succeeded == 0 else "PARTIAL")
    durable_run.finished_at = datetime.now(UTC)
    durable_run.counts = {
        "attempted": len(entity_ids),
        "succeeded": succeeded,
        "failed": failed,
        "observations_added": observations_added,
    }
    durable_run.failure_details = (
        {"failures": [failure.as_dict() for failure in failures]} if failures else None
    )
    session.commit()

    return BatchIngestionResult(
        run_id=run_id,
        attempted=len(entity_ids),
        succeeded=succeeded,
        failed=failed,
        observations_added=observations_added,
        failures=tuple(failures),
    )


def derive_quarter(session: Session, quarter: str) -> int:
    changed = 0
    for entity in session.scalars(select(Entity).where(Entity.is_eligible.is_(True))).all():
        rows = session.scalars(
            select(Observation)
            .where(
                Observation.entity_id == entity.id,
                Observation.observed_at < _quarter_end_exclusive(quarter),
            )
            .order_by(Observation.observed_at.desc())
        ).all()
        latest: dict[str, Observation] = {}
        for row in rows:
            latest.setdefault(row.metric_key, row)
        for key, row in latest.items():
            if isinstance(row.raw_value, bool) or not isinstance(row.raw_value, (int, float)):
                continue
            current = session.scalar(
                select(DerivedMetric).where(
                    DerivedMetric.entity_id == entity.id,
                    DerivedMetric.metric_key == key,
                    DerivedMetric.quarter == quarter,
                    DerivedMetric.algorithm_version == ROLLUP_VERSION,
                )
            )
            provenance = {
                "observation_id": str(row.id),
                "evidence_id": str(row.evidence_id),
                "source_url": row.source_url,
                "observed_at": row.observed_at.isoformat(),
            }
            if current is None:
                session.add(
                    DerivedMetric(
                        entity_id=entity.id,
                        metric_key=key,
                        value=float(row.raw_value),
                        quarter=quarter,
                        algorithm_version=ROLLUP_VERSION,
                        provenance=provenance,
                    )
                )
            else:
                current.value = float(row.raw_value)
                current.provenance = provenance
                current.computed_at = datetime.now(UTC)
            changed += 1
    session.commit()
    return changed


def _candidate_metrics(
    session: Session, quarter: str
) -> tuple[list[CandidateMetrics], bool, list[tuple[str, float, float]]]:
    rows = session.scalars(
        select(DerivedMetric).where(
            DerivedMetric.quarter == quarter,
            DerivedMetric.algorithm_version == ROLLUP_VERSION,
        )
    ).all()
    values: defaultdict[UUID, dict[str, float | int | None]] = defaultdict(dict)
    complete = True
    for row in rows:
        values[row.entity_id][row.metric_key] = row.value
        complete = complete and bool(row.provenance.get("evidence_id"))
    ids = list(values)
    eligible: dict[UUID, bool] = {}
    if ids:
        eligible = {
            entity.id: entity.is_eligible
            for entity in session.scalars(select(Entity).where(Entity.id.in_(ids))).all()
        }
    candidates = [
        CandidateMetrics(entity_id, metrics, eligible.get(entity_id, False))
        for entity_id, metrics in values.items()
    ]
    previous_rows = session.scalars(
        select(DerivedMetric).where(
            DerivedMetric.quarter == _previous_quarter(quarter),
            DerivedMetric.algorithm_version == ROLLUP_VERSION,
        )
    ).all()
    previous = {(row.entity_id, row.metric_key): row.value for row in previous_rows}
    pairs = [
        (
            f"{row.entity_id}:{row.metric_key}",
            previous[(row.entity_id, row.metric_key)],
            row.value,
        )
        for row in rows
        if (row.entity_id, row.metric_key) in previous
    ]
    return candidates, complete, pairs


@dataclass(frozen=True)
class SnapshotEvaluation:
    category: RankingCategory
    algorithm: AlgorithmDefinition
    spec: AlgorithmSpec
    rows: list[ScoredCandidate]
    report: ValidationReport


def evaluate_snapshot(session: Session, slug: str, quarter: str) -> SnapshotEvaluation:
    category, algorithm, spec = ensure_category_and_algorithm(session, slug)
    candidates, complete, pairs = _candidate_metrics(session, quarter)
    raw_rows = RankingEngine().run(spec, candidates)
    rows = [row for row in raw_rows if row.qualified]
    rows.sort(key=lambda row: (-row.score, str(row.entity_id)))
    rows = [
        ScoredCandidate(
            row.entity_id,
            row.score,
            index,
            row.factor_breakdown,
            row.factor_coverage,
            True,
        )
        for index, row in enumerate(rows, 1)
    ]
    report = QuarterValidator().validate(
        ValidationInput(
            complete,
            False,
            algorithm.version,
            spec.version,
            [row.rank for row in rows],
            [row.factor_coverage for row in rows],
            pairs,
            spec.minimum_factor_coverage,
        )
    )
    if not rows:
        report = ValidationReport(
            errors=report.errors + ("no_qualified_candidates",),
            blocking_anomalies=report.blocking_anomalies,
        )
    return SnapshotEvaluation(category, algorithm, spec, rows, report)


def validate_quarter(session: Session, slug: str, quarter: str) -> ValidationReport:
    return evaluate_snapshot(session, slug, quarter).report


def _persist_scored_rows(session: Session, run: RankingRun, rows: list[ScoredCandidate], quarter: str) -> None:
    for row in rows:
        session.add(
            RankingResult(
                ranking_run_id=run.id,
                entity_id=row.entity_id,
                score=row.score,
                rank=row.rank,
                confidence=1.0,
                factor_breakdown={
                    key: {
                        "raw_value": value.raw_value,
                        "normalized_value": value.normalized_value,
                        "weight": value.weight,
                        "contribution": value.contribution,
                        "missing_policy": value.missing_policy,
                    }
                    for key, value in row.factor_breakdown.items()
                },
                provenance_summary={
                    "quarter": quarter,
                    "rollup_version": ROLLUP_VERSION,
                    "factor_coverage": row.factor_coverage,
                },
            )
        )


def _reviewed_pool_count(session: Session) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(Entity)
            .where(
                Entity.is_eligible.is_(True),
                Entity.review_status == ReviewStatus.APPROVED,
            )
        )
        or 0
    )


def create_provisional_run(
    session: Session,
    slug: str,
    quarter: str,
    cutoff_at: datetime,
) -> RankingRun:
    if cutoff_at.tzinfo is None:
        raise ValueError("cutoff_at must be timezone-aware")
    evaluation = evaluate_snapshot(session, slug, quarter)
    if not evaluation.rows:
        raise ValueError("cannot create provisional ranking without qualified candidates")
    run = RankingRun(
        category_id=evaluation.category.id,
        algorithm_id=evaluation.algorithm.id,
        quarter=quarter,
        status=RankingRunStatus.PROVISIONAL,
        started_at=datetime.now(UTC),
        cutoff_at=cutoff_at,
        candidate_count=_reviewed_pool_count(session),
        validation_details={
            "official": False,
            "validation_ok": evaluation.report.ok,
            "errors": list(evaluation.report.errors),
            "blocking_anomalies": list(evaluation.report.blocking_anomalies),
            "ranked_count": len(evaluation.rows),
            "algorithm_version": evaluation.algorithm.version,
        },
    )
    session.add(run)
    session.flush()
    _persist_scored_rows(session, run, evaluation.rows, quarter)
    session.commit()
    session.refresh(run)
    return run


def publish_quarter(session: Session, slug: str, quarter: str) -> RankingRun:
    evaluation = evaluate_snapshot(session, slug, quarter)
    run = RankingRun(
        category_id=evaluation.category.id,
        algorithm_id=evaluation.algorithm.id,
        quarter=quarter,
        status=RankingRunStatus.DRAFT,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.flush()
    run.status = RankingRunStatus.VALIDATING
    if not evaluation.report.ok:
        run.status = RankingRunStatus.FAILED
        run.failure_details = {
            "errors": list(evaluation.report.errors),
            "blocking_anomalies": list(evaluation.report.blocking_anomalies),
        }
        session.commit()
        raise ValueError(f"Quarter validation failed: {run.failure_details}")
    _persist_scored_rows(session, run, evaluation.rows, quarter)
    run.status = RankingRunStatus.PUBLISHED
    run.published_at = datetime.now(UTC)
    session.commit()
    return run
