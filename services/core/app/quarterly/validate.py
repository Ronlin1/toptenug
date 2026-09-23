from __future__ import annotations

import math
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ValidationCandidate:
    entity_id: UUID
    score: float
    rank: int
    factor_coverage: float
    provenance_count: int
    current_metric: float | None = None
    previous_metric: float | None = None


@dataclass(frozen=True)
class ValidationReport:
    blocking_reasons: tuple[str, ...]
    blocking_anomalies: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.blocking_reasons and not self.blocking_anomalies


class QuarterValidator:
    def __init__(self, *, minimum_factor_coverage: float = 0.60, jump_ratio_threshold: float = 10.0) -> None:
        self.minimum_factor_coverage = minimum_factor_coverage
        self.jump_ratio_threshold = jump_ratio_threshold

    def validate(self, candidates: list[ValidationCandidate]) -> ValidationReport:
        reasons: list[str] = []
        anomalies: list[str] = []
        ranks: set[int] = set()
        for candidate in candidates:
            if candidate.rank < 1:
                reasons.append(f"{candidate.entity_id}: rank must be positive")
            if candidate.rank in ranks:
                reasons.append(f"duplicate rank: {candidate.rank}")
            ranks.add(candidate.rank)
            if not math.isfinite(candidate.score):
                reasons.append(f"{candidate.entity_id}: score is not finite")
            if candidate.factor_coverage < self.minimum_factor_coverage:
                reasons.append(f"{candidate.entity_id}: factor coverage below minimum")
            if candidate.provenance_count < 1:
                reasons.append(f"{candidate.entity_id}: missing provenance")
            if (
                candidate.current_metric is not None
                and candidate.previous_metric is not None
                and candidate.previous_metric > 0
                and candidate.current_metric / candidate.previous_metric >= self.jump_ratio_threshold
            ):
                anomalies.append(f"{candidate.entity_id}: metric jump {candidate.current_metric / candidate.previous_metric:.2f}x")
        if not candidates:
            reasons.append("candidate set is empty")
        return ValidationReport(tuple(reasons), tuple(anomalies))
