from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from .enums import EntityType, ReviewStatus, UgandaRelation


class EntityCreate(BaseModel):
    name: str = Field(min_length=1)
    entity_type: EntityType
    is_discoverable: bool = True
    is_eligible: bool = False
    uganda_relation: UgandaRelation | None = None
    review_status: ReviewStatus = ReviewStatus.PENDING


class ObservationInput(BaseModel):
    metric_key: str = Field(min_length=1)
    raw_value: float | int | str
    observed_at: datetime
    source_url: HttpUrl
    evidence_id: UUID
    source_record_id: str | None = None
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
