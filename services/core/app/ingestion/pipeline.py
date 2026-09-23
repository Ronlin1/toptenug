from __future__ import annotations

from app.domain.schemas import ObservationInput


class InMemoryObservationStore:
    """Reference idempotency behavior used by ingestion orchestration and fixture tests."""

    def __init__(self) -> None:
        self.rows: list[ObservationInput] = []
        self._by_key: dict[tuple[str | None, str, object], ObservationInput] = {}

    def add(self, observation: ObservationInput) -> ObservationInput:
        key = (observation.source_record_id, observation.metric_key, observation.observed_at)
        existing = self._by_key.get(key)
        if existing is not None:
            return existing
        self._by_key[key] = observation
        self.rows.append(observation)
        return observation

    def add_many(self, observations: list[ObservationInput]) -> list[ObservationInput]:
        return [self.add(observation) for observation in observations]
