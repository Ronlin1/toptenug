from app.domain.enums import EntityType
from app.domain.schemas import CandidateProposal, DiscoveryQuery
from app.intelligence.base import proposal_to_candidate_record


def test_candidate_proposal_has_no_official_rank_field():
    assert "rank" not in CandidateProposal.model_fields
    assert "official_score" not in CandidateProposal.model_fields


def test_discovery_order_is_not_persisted_as_rank():
    proposals = [
        CandidateProposal(
            display_name="First Search Result",
            entity_type=EntityType.PERSON,
            candidate_profiles={"github": "first"},
            uganda_relation_claims=["Ugandan developer"],
            source_urls=["https://example.com/first"],
            confidence=0.9,
        ),
        CandidateProposal(
            display_name="Second Search Result",
            entity_type=EntityType.PERSON,
            candidate_profiles={"github": "second"},
            uganda_relation_claims=["Ugandan developer"],
            source_urls=["https://example.com/second"],
            confidence=0.8,
        ),
    ]
    saved = [proposal_to_candidate_record(proposal) for proposal in proposals]
    assert all(row["official_rank"] is None for row in saved)
    assert all(row["official_score"] is None for row in saved)


def test_discovery_query_is_just_research_input():
    query = DiscoveryQuery(text="Ugandan open source developers")
    assert query.text.startswith("Ugandan")
