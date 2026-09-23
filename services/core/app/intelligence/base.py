from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums import EntityType, ReviewStatus

T = TypeVar("T", bound=BaseModel)


class DiscoveryQuery(BaseModel):
    text: str = Field(min_length=3)


class CandidateProposal(BaseModel):
    display_name: str = Field(min_length=1)
    entity_type: EntityType
    candidate_profiles: dict[str, str] = Field(default_factory=dict)
    uganda_relation_claims: list[str] = Field(default_factory=list)
    source_urls: list[HttpUrl] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    review_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED


class CandidateProposalBatch(BaseModel):
    candidates: list[CandidateProposal]


@dataclass(frozen=True)
class CandidateDraft:
    proposal: CandidateProposal
    official_rank: int | None = None


class CandidateRepository:
    """Minimal draft repository boundary; official rank is never accepted from discovery."""

    def __init__(self) -> None:
        self.rows: list[CandidateDraft] = []

    def save_candidate_proposals(self, proposals: list[CandidateProposal]) -> list[CandidateDraft]:
        created = [CandidateDraft(proposal=proposal) for proposal in proposals]
        self.rows.extend(created)
        return created


class IntelligenceProvider(Protocol):
    def discover(self, query: DiscoveryQuery) -> list[CandidateProposal]: ...

    def extract_evidence(self, url: str, schema: type[T]) -> list[T]: ...
