from collections.abc import Iterable
from uuid import UUID

from app.ranking.engine import CandidateMetrics

from .pipeline import InMemoryIngestionRepository, StoredObservation


def _latest(
    rows: Iterable[StoredObservation], entity_id: UUID
) -> dict[str, StoredObservation]:
    out: dict[str, StoredObservation] = {}
    for row in rows:
        if row.entity_id != entity_id:
            continue
        current = out.get(row.metric_key)
        if current is None or row.observed_at > current.observed_at:
            out[row.metric_key] = row
    return out


def derive_candidate_metrics(
    repo: InMemoryIngestionRepository,
    entity_id: UUID,
    *,
    eligible: bool,
) -> CandidateMetrics:
    latest = _latest(repo.observations, entity_id)
    metrics: dict[str, float | int | None] = {
        key: float(row.raw_value)
        for key, row in latest.items()
        if isinstance(row.raw_value, (int, float))
        and not isinstance(row.raw_value, bool)
    }
    return CandidateMetrics(entity_id, metrics, eligible)
