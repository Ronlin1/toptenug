from __future__ import annotations

from typing import Protocol
from uuid import UUID


class MetricCandidate(Protocol):
    entity_id: UUID
    metrics: dict[str, float | int | None]


def metric_value(candidate: MetricCandidate, metric_key: str) -> float | None:
    value = candidate.metrics.get(metric_key)
    return None if value is None else float(value)
