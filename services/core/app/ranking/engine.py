from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.enums import RankingType
from app.ranking.index import weighted_index_score
from app.ranking.loader import AlgorithmSpec
from app.ranking.normalizers import normalize


@dataclass(frozen=True)
class CandidateMetrics:
    entity_id: UUID
    metrics: dict[str, float | int | None]
    eligible: bool = True


@dataclass(frozen=True)
class FactorScore:
    normalized: float | None
    weight: float
    missing: bool
    missing_policy: str


@dataclass(frozen=True)
class ScoredCandidate:
    entity_id: UUID
    score: float
    rank: int
    factor_breakdown: dict[str, FactorScore]
    factor_coverage: float
    meets_minimum_coverage: bool


class RankingEngine:
    def run(self, spec: AlgorithmSpec, candidates: list[CandidateMetrics]) -> list[ScoredCandidate]:
        if spec.ranking_type != RankingType.INDEX:
            raise ValueError("RankingEngine.run currently requires an INDEX AlgorithmSpec")

        active = [candidate for candidate in candidates if candidate.eligible]
        normalized_by_factor: dict[str, dict[UUID, float]] = {}

        for factor in spec.factors:
            present = [
                (candidate.entity_id, float(candidate.metrics[factor.metric]))
                for candidate in active
                if candidate.metrics.get(factor.metric) is not None
            ]
            values = normalize(factor.normalization, [value for _, value in present])
            normalized_by_factor[factor.name] = {
                entity_id: value for (entity_id, _), value in zip(present, values, strict=True)
            }

        preliminary: list[tuple[CandidateMetrics, float, dict[str, FactorScore], float, bool]] = []
        total_weight = sum(factor.weight for factor in spec.factors)
        for candidate in active:
            available: list[tuple[float, float]] = []
            breakdown: dict[str, FactorScore] = {}
            available_weight = 0.0
            for factor in spec.factors:
                normalized = normalized_by_factor[factor.name].get(candidate.entity_id)
                missing = normalized is None
                breakdown[factor.name] = FactorScore(
                    normalized=normalized,
                    weight=factor.weight,
                    missing=missing,
                    missing_policy=spec.missing_data_policy,
                )
                if normalized is not None:
                    available.append((factor.weight, normalized))
                    available_weight += factor.weight
            coverage = 0.0 if total_weight == 0 else available_weight / total_weight
            score = weighted_index_score(available)
            preliminary.append((candidate, score, breakdown, coverage, coverage >= spec.minimum_factor_coverage))

        ordered = sorted(preliminary, key=lambda row: (-round(row[1], 12), str(row[0].entity_id)))
        return [
            ScoredCandidate(
                entity_id=candidate.entity_id,
                score=round(score, 8),
                rank=index,
                factor_breakdown=breakdown,
                factor_coverage=coverage,
                meets_minimum_coverage=meets_coverage,
            )
            for index, (candidate, score, breakdown, coverage, meets_coverage) in enumerate(ordered, start=1)
        ]
