from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.store import EntityPublicRecord, public_store
from app.domain.enums import RankingRunStatus, RankingType
from app.main import app
from app.quarterly.publish import PublishedResult, PublishedRun, Quarter

client = TestClient(app)
CATEGORY = UUID(int=100)


@pytest.fixture(autouse=True)
def _seed_store():
    public_store.reset()
    public_store.register_category(
        slug="github-developers",
        name="Top Ugandan GitHub Developers",
        category_id=CATEGORY,
        ranking_type=RankingType.INDEX,
        methodology_slug="devrankug-v1",
    )
    for i in range(1, 16):
        entity_id = UUID(int=i)
        public_store.register_entity(
            EntityPublicRecord(
                id=entity_id,
                slug=f"person-{i}",
                name=f"Person {i}",
                evidence_urls=[f"https://example.com/person-{i}"],
            )
        )

    published = PublishedRun(
        id=UUID(int=1),
        category_id=CATEGORY,
        quarter=Quarter(2026, 3),
        algorithm_name="DevRankUG",
        algorithm_version="1.0.0",
        status=RankingRunStatus.PUBLISHED,
        started_at=datetime(2026, 9, 30, tzinfo=UTC),
        published_at=datetime(2026, 9, 30, tzinfo=UTC),
    )
    public_store.ranking_store.runs[published.id] = published
    public_store.ranking_store.results[published.id] = tuple(
        PublishedResult(
            id=UUID(int=1000 + i),
            ranking_run_id=published.id,
            entity_id=UUID(int=i),
            rank=i,
            score=100 - i,
            factor_breakdown={},
            factor_coverage=1.0,
            confidence=0.9,
        )
        for i in range(1, 16)
    )
    public_store.ranking_store.official_by_category[CATEGORY] = published.id

    draft = PublishedRun(
        id=UUID(int=2),
        category_id=CATEGORY,
        quarter=Quarter(2026, 4),
        algorithm_name="DevRankUG",
        algorithm_version="1.0.0",
        status=RankingRunStatus.DRAFT,
        started_at=datetime(2026, 12, 31, tzinfo=UTC),
    )
    public_store.ranking_store.runs[draft.id] = draft
    yield
    public_store.reset()


@pytest.mark.parametrize("limit", [10, 20, 30, 50])
def test_supported_public_limits(limit):
    response = client.get(f"/v1/rankings/github-developers?limit={limit}")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) <= limit
    assert payload["quarter"] == "2026-Q3"
    assert payload["results"][0]["ranking_result_id"]
    assert payload["results"][0]["provenance"]["source_count"] == 1


def test_limit_above_50_is_rejected():
    assert client.get("/v1/rankings/github-developers?limit=51").status_code == 422


def test_draft_runs_are_never_public():
    response = client.get("/v1/rankings/github-developers?quarter=2026-Q4")
    assert response.status_code == 404
