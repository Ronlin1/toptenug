from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.enums import EntityType
from app.domain.schemas import EntityCreate, ObservationInput


def test_observation_requires_source_url_and_evidence_id():
    with pytest.raises(ValidationError):
        ObservationInput(
            metric_key="github.followers",
            raw_value=120,
            observed_at=datetime.now(UTC),
        )


def test_entity_can_be_discoverable_without_being_eligible():
    entity = EntityCreate(name="Example", entity_type=EntityType.PERSON)
    assert entity.is_discoverable is True
    assert entity.is_eligible is False
