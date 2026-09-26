from datetime import UTC, datetime
from uuid import UUID

from app.domain.enums import EntityType
from app.domain.schemas import CandidateProposal, ObservationInput
from app.ingestion.entity_resolution import EntityResolutionService
from app.ingestion.pipeline import InMemoryIngestionRepository

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


def _proposal(name: str, profile: str | None = None) -> CandidateProposal:
    return CandidateProposal(
        display_name=name,
        entity_type=EntityType.PERSON,
        candidate_profiles={"github": profile} if profile else {},
        uganda_relation_claims=["Ugandan developer"],
        source_urls=[profile or "https://example.com/evidence"],
        confidence=0.95,
    )


def test_ingestion_is_idempotent_and_never_mutates_existing_observation():
    repo = InMemoryIngestionRepository()
    entity = repo.create_entity(_proposal("Example", "https://github.com/example"))
    assert repo.save_observation(entity.id, _observation(10)) is True
    assert repo.save_observation(entity.id, _observation(99)) is False
    assert repo.observations[0].raw_value == 10
    assert len(repo.observations) == 1


def test_ambiguous_name_match_refuses_auto_merge():
    repo = InMemoryIngestionRepository()
    repo.create_entity(_proposal("Ronnie", "https://github.com/ronnie-one"))
    repo.create_entity(_proposal("Ronnie", "https://github.com/ronnie-two"))
    result = EntityResolutionService(repo).resolve(_proposal("Ronnie"))
    assert result.entity_id is None
    assert result.review_required is True
    assert result.reason == "name_only_match"


def test_exact_external_profile_identifier_can_auto_link():
    repo = InMemoryIngestionRepository()
    entity = repo.create_entity(_proposal("Ronnie", "https://github.com/ronlin1"))
    result = EntityResolutionService(repo).resolve(
        _proposal("Different Name", "https://github.com/ronlin1")
    )
    assert result.entity_id == entity.id
    assert result.review_required is False
    assert result.reason == "exact_profile"
