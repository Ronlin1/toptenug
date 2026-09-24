from dataclasses import dataclass
from uuid import UUID
from app.domain.enums import ReviewStatus,UgandaRelation
from app.domain.schemas import EligibilityDecision
@dataclass(frozen=True)
class EligibilityEvidence:
    evidence_id:UUID
    relation:UgandaRelation
    confidence:float
class EligibilityService:
    def __init__(self,*,min_confidence:float=.8)->None:self.min_confidence=min_confidence
    def evaluate(self,evidence:list[EligibilityEvidence])->EligibilityDecision:
        if not evidence:return EligibilityDecision(eligible=False,status=ReviewStatus.PENDING)
        strong=[e for e in evidence if e.confidence>=self.min_confidence]
        if not strong:return EligibilityDecision(eligible=False,evidence_ids=[e.evidence_id for e in evidence],status=ReviewStatus.REVIEW_REQUIRED)
        relations={e.relation for e in strong}
        if len(relations)!=1:return EligibilityDecision(eligible=False,evidence_ids=[e.evidence_id for e in strong],status=ReviewStatus.REVIEW_REQUIRED)
        relation=next(iter(relations));return EligibilityDecision(eligible=True,relation=relation,evidence_ids=[e.evidence_id for e in strong],status=ReviewStatus.APPROVED)
