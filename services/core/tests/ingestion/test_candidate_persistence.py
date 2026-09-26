from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.enums import EntityType, ReviewStatus, UgandaRelation
from app.domain.models import Base, CandidateRecord, Entity, Evidence, SourceAccount
from app.domain.schemas import CandidateProposal
from app.ingestion.candidates import (
    approve_candidate,
    list_review_queue,
    persist_candidate_proposals,
    reject_candidate,
)


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def proposal(name: str, github: str, confidence: float = 0.95) -> CandidateProposal:
    return CandidateProposal(
        display_name=name,
        entity_type=EntityType.PERSON,
        candidate_profiles={
            "github": github,
            "website": f"https://{name.lower().replace(' ', '')}.example",
        },
        uganda_relation_claims=["Public source states this person is Ugandan"],
        source_urls=[f"https://evidence.example/{name.lower().replace(' ', '-') }"],
        confidence=confidence,
        review_status=ReviewStatus.PENDING,
    )


def test_persist_candidates_deduplicates_same_github_identity_independent_of_order() -> None:
    with make_session() as session:
        first = proposal("Alice One", "https://github.com/AliceUG")
        duplicate = proposal("Alice Alias", "aliceug")
        bob = proposal("Bob Two", "https://github.com/bobug")

        summary_one = persist_candidate_proposals(session, [first, bob], "gemini-search")
        summary_two = persist_candidate_proposals(session, [duplicate, bob, first], "manual-seed")

        rows = session.scalars(select(CandidateRecord).order_by(CandidateRecord.normalized_identity_key)).all()
        assert summary_one.created == 2
        assert summary_two.created == 0
        assert summary_two.deduplicated == 3
        assert len(rows) == 2
        assert {row.github_login for row in rows} == {"aliceug", "bobug"}
        assert all(not hasattr(row, "rank") and not hasattr(row, "official_score") for row in rows)


def test_low_confidence_candidate_enters_review_required_queue() -> None:
    with make_session() as session:
        candidate = proposal("Cautious Candidate", "cautious-ug", confidence=0.5)
        candidate = candidate.model_copy(update={"review_status": ReviewStatus.REVIEW_REQUIRED})

        persist_candidate_proposals(session, [candidate], "gemini-search")

        queue = list_review_queue(session, ReviewStatus.REVIEW_REQUIRED)
        assert len(queue) == 1
        assert queue[0].display_name == "Cautious Candidate"


def test_approval_creates_eligible_person_source_account_and_reviewed_evidence() -> None:
    with make_session() as session:
        persist_candidate_proposals(
            session,
            [proposal("Grace Builder", "https://github.com/grace-ug")],
            "gemini-search",
        )
        candidate = session.scalar(select(CandidateRecord))
        assert candidate is not None

        entity = approve_candidate(
            session,
            candidate.id,
            UgandaRelation.UGANDAN_IN_UGANDA,
            "Reviewed first-party/public evidence.",
        )

        refreshed = session.get(CandidateRecord, candidate.id)
        assert refreshed is not None
        assert refreshed.review_status is ReviewStatus.APPROVED
        assert refreshed.resolved_entity_id == entity.id
        assert entity.entity_type is EntityType.PERSON
        assert entity.is_eligible is True
        assert entity.uganda_relation is UgandaRelation.UGANDAN_IN_UGANDA
        assert entity.review_status is ReviewStatus.APPROVED
        assert session.scalar(select(SourceAccount).where(SourceAccount.entity_id == entity.id)) is not None
        evidence = session.scalars(select(Evidence).where(Evidence.entity_id == entity.id)).all()
        assert evidence
        assert all(row.review_status is ReviewStatus.APPROVED for row in evidence)


def test_approval_rejects_non_ugandan_relation_for_ugandan_developer_category() -> None:
    with make_session() as session:
        persist_candidate_proposals(session, [proposal("Visitor Dev", "visitor-dev")], "manual-seed")
        candidate = session.scalar(select(CandidateRecord))
        assert candidate is not None

        try:
            approve_candidate(
                session,
                candidate.id,
                UgandaRelation.UGANDA_BASED_NON_UGANDAN,
                "Not eligible for this category.",
            )
        except ValueError as exc:
            assert "UGANDAN_IN_UGANDA or UGANDAN_DIASPORA" in str(exc)
        else:
            raise AssertionError("approval must reject non-Ugandan relation for this category")


def test_reject_candidate_keeps_record_auditable_without_creating_entity() -> None:
    with make_session() as session:
        persist_candidate_proposals(session, [proposal("Rejected Dev", "rejected-dev")], "manual-seed")
        candidate = session.scalar(select(CandidateRecord))
        assert candidate is not None

        rejected = reject_candidate(session, candidate.id, "Evidence did not establish eligibility.")

        assert rejected.review_status is ReviewStatus.REJECTED
        assert rejected.reviewer_note == "Evidence did not establish eligibility."
        assert rejected.resolved_entity_id is None
        assert session.scalar(select(Entity)) is None
