from uuid import UUID

from app.domain.enums import ReviewStatus, UgandaRelation
from app.ingestion.eligibility import EligibilityEvidence, EligibilityService


def test_conflicting_uganda_evidence_blocks_official_eligibility():
    decision = EligibilityService().evaluate([
        EligibilityEvidence(evidence_id=UUID(int=1), relation=UgandaRelation.UGANDAN_IN_UGANDA, confidence=0.95),
        EligibilityEvidence(evidence_id=UUID(int=2), relation=UgandaRelation.UGANDAN_DIASPORA, confidence=0.95),
    ])
    assert decision.eligible is False
    assert decision.status == ReviewStatus.REVIEW_REQUIRED


def test_single_high_confidence_relation_is_eligible():
    decision = EligibilityService().evaluate([
        EligibilityEvidence(evidence_id=UUID(int=1), relation=UgandaRelation.UGANDAN_IN_UGANDA, confidence=0.95),
    ])
    assert decision.eligible is True
    assert decision.status == ReviewStatus.APPROVED
