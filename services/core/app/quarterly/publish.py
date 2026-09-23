from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.enums import RankingRunStatus
from app.quarterly.validate import QuarterValidator, ValidationCandidate


@dataclass(frozen=True, order=True)
class Quarter:
    year: int
    number: int

    def __post_init__(self) -> None:
        if self.number not in {1, 2, 3, 4}:
            raise ValueError("Quarter number must be 1..4")

    def __str__(self) -> str:
        return f"{self.year}-Q{self.number}"


@dataclass(frozen=True)
class PublishedRun:
    id: UUID
    quarter: Quarter
    category_id: UUID
    algorithm_version: str
    status: RankingRunStatus
    results: tuple[ValidationCandidate, ...]
    published_at: datetime | None
    failure_reasons: tuple[str, ...] = ()


class QuarterValidationError(RuntimeError):
    pass


class QuarterPublisher:
    """Atomic publication behavior; database transaction adapters can wrap this boundary."""

    def __init__(self, validator: QuarterValidator | None = None) -> None:
        self.validator = validator or QuarterValidator()
        self._candidates: list[ValidationCandidate] = []
        self._official: dict[UUID, PublishedRun] = {}
        self.failed_runs: list[PublishedRun] = []

    def set_candidates(self, candidates: list[ValidationCandidate]) -> None:
        self._candidates = list(candidates)

    def publish(self, quarter: Quarter, category_id: UUID, algorithm_version: str) -> PublishedRun:
        snapshot = tuple(self._candidates)
        report = self.validator.validate(list(snapshot))
        if not report.ok:
            failed = PublishedRun(
                id=uuid4(), quarter=quarter, category_id=category_id,
                algorithm_version=algorithm_version, status=RankingRunStatus.FAILED,
                results=snapshot, published_at=None,
                failure_reasons=report.blocking_reasons + report.blocking_anomalies,
            )
            self.failed_runs.append(failed)
            raise QuarterValidationError("; ".join(failed.failure_reasons))
        run = PublishedRun(
            id=uuid4(), quarter=quarter, category_id=category_id,
            algorithm_version=algorithm_version, status=RankingRunStatus.PUBLISHED,
            results=snapshot, published_at=datetime.now(UTC),
        )
        self._official[category_id] = run
        return run

    def current_official(self, category_id: UUID) -> PublishedRun:
        return self._official[category_id]
