from sqlalchemy import inspect

from app.domain.enums import RankingRunStatus
from app.domain.models import CandidateRecord, RankingRun


def test_provisional_run_status_is_persisted_contract() -> None:
    assert RankingRunStatus.PROVISIONAL.value == "PROVISIONAL"


def test_candidate_record_contains_reviewable_discovery_fields() -> None:
    columns = set(inspect(CandidateRecord).columns.keys())
    assert {
        "id",
        "normalized_identity_key",
        "display_name",
        "github_login",
        "github_profile_url",
        "profile_map",
        "proposed_uganda_relation",
        "confidence",
        "source_urls",
        "discovery_source",
        "discovered_at",
        "review_status",
        "resolved_entity_id",
        "reviewer_note",
    } <= columns


def test_ranking_run_contains_live_snapshot_metadata() -> None:
    columns = set(inspect(RankingRun).columns.keys())
    assert {"cutoff_at", "candidate_count", "validation_details"} <= columns
