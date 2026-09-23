from datetime import UTC, datetime
from uuid import UUID

from app.domain.schemas import ObservationInput
from app.ingestion.entity_resolution import EntityIdentity, EntityResolutionService
from app.ingestion.pipeline import InMemoryObservationStore

NOW = datetime(2026, 9, 23, tzinfo=UTC)


def _observation(value=10):
    return ObservationInput(
        metric_key="github.followers",
        raw_value=value,
        observed_at=NOW,
        source_url="https://github.com/example",
        evidence_id=UUID(int=1),
        source_record_id="example:github.followers",
    )


def test_ingestion_is_idempotent_and_never_mutates_existing_observation():
    store = InMemoryObservationStore()
    first = store.add(_observation(10))
    second = store.add(_observation(99))
    assert first is second
    assert first.raw_value == 10
    assert len(store.rows) == 1


def test_ambiguous_alias_match_refuses_auto_merge():
    result = EntityResolutionService().resolve(
        candidate=EntityIdentity(aliases={"Ronnie"}, profiles={}),
        existing=[
            (UUID(int=1), EntityIdentity(aliases={"Ronnie"}, profiles={})),
            (UUID(int=2), EntityIdentity(aliases={"Ronnie"}, profiles={})),
        ],
    )
    assert result.entity_id is None
    assert result.review_required is True


def test_exact_external_profile_identifier_can_auto_link():
    result = EntityResolutionService().resolve(
        candidate=EntityIdentity(aliases={"Different Name"}, profiles={"github": "ronlin1"}),
        existing=[(UUID(int=1), EntityIdentity(aliases={"Ronnie"}, profiles={"github": "ronlin1"}))],
    )
    assert result.entity_id == UUID(int=1)
    assert result.review_required is False
