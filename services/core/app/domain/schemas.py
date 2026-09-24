from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from .enums import EntityType, EvidenceLevel, ReviewStatus, UgandaRelation
class EntityCreate(BaseModel):
    name: str = Field(min_length=1,max_length=250); entity_type: EntityType; slug: str|None=None; is_discoverable: bool=True; is_eligible: bool=False; uganda_relation: UgandaRelation|None=None
class EntityRef(BaseModel): id: UUID; external_id: str
class EvidenceInput(BaseModel):
    level: EvidenceLevel; source_url: HttpUrl; retrieved_at: datetime; claim: str; confidence: float=Field(ge=0,le=1); content_hash: str|None=None
class ObservationInput(BaseModel):
    metric_key: str=Field(min_length=1); raw_value: float|int|str; observed_at: datetime; source_url: str=Field(min_length=1); evidence_id: UUID; source_record_id: str|None=None
class CandidateProposal(BaseModel):
    model_config=ConfigDict(extra="forbid")
    display_name: str; entity_type: EntityType; candidate_profiles: dict[str,str]=Field(default_factory=dict); uganda_relation_claims: list[str]=Field(default_factory=list); source_urls: list[str]=Field(default_factory=list); confidence: float=Field(ge=0,le=1); review_status: ReviewStatus=ReviewStatus.PENDING
class DiscoveryQuery(BaseModel): text: str=Field(min_length=1)
class EligibilityDecision(BaseModel):
    eligible: bool; relation: UgandaRelation|None=None; evidence_ids: list[UUID]=Field(default_factory=list); status: ReviewStatus
class PublicEvidence(BaseModel): claim: str; source_url: str; level: EvidenceLevel; confidence: float
class ApiModel(BaseModel): model_config=ConfigDict(from_attributes=True)
JsonValue = dict[str,Any]|list[Any]|str|int|float|bool|None
