from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.domain.enums import RankingType


@dataclass(frozen=True)
class FactorSpec:
    name: str
    weight: float
    metric: str
    normalization: str


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    version: str
    ranking_type: RankingType
    eligibility_policy: str
    missing_data_policy: str
    minimum_factor_coverage: float
    tie_breaker: str
    factors: tuple[FactorSpec, ...]


def load_algorithm_spec(path: Path) -> AlgorithmSpec:
    raw = yaml.safe_load(path.read_text())
    factors = tuple(
        FactorSpec(
            name=name,
            weight=float(config["weight"]),
            metric=config["metric"],
            normalization=config["normalization"],
        )
        for name, config in raw.get("factors", {}).items()
    )
    return AlgorithmSpec(
        name=raw["name"],
        version=str(raw["version"]),
        ranking_type=RankingType(raw["ranking_type"]),
        eligibility_policy=raw["eligibility_policy"],
        missing_data_policy=raw["missing_data_policy"],
        minimum_factor_coverage=float(raw["minimum_factor_coverage"]),
        tie_breaker=raw["tie_breaker"],
        factors=factors,
    )
