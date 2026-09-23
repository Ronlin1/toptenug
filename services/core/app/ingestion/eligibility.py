from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.enums import ReviewStatus, UgandaRelation


@dataclass(frozen=True)
class EligibilityEvidence:
    evidence_id: UUID
    relation: UgandaRelation
    confidence: float


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    relation: UgandaRelation | None
    evidence_ids: list[UUID]
    status: ReviewStatus


class EligibilityService:
    def __init__(self, approval_threshold: float = 0.85) -> None:
        self.approval_threshold = approval_threshold

    def evaluate(self, evidence: list[EligibilityEvidence]) -> EligibilityDecision:
        if not evidence:
            return EligibilityDecision(False, None, [], ReviewStatus.PENDING)
        strong = [item for item in evidence if item.confidence >= self.approval_threshold]
        relations = {item.relation for item in strong}
        evidence_ids = [item.evidence_id for item in evidence]
        if len(relations) != 1:
            return EligibilityDecision(False, None, evidence_ids, ReviewStatus.REVIEW_REQUIRED)
        relation = next(iter(relations))
        return EligibilityDecision(True, relation, evidence_ids, ReviewStatus.APPROVED)
