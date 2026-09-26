from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.store import EntityPublicRecord, public_store
from app.domain.enums import RankingRunStatus, RankingType
from app.main import app
from app.quarterly.publish import PublishedResult, PublishedRun, Quarter

client = TestClient(app)
CATEGORY = UUID(int=200)
ENTITY = UUID(int=7)


def test_share_metadata_comes_from_immutable_published_result():
    public_store.reset()
    public_store.register_category(
        slug="github-developers",
        name="Top Ugandan GitHub Developers",
        category_id=CATEGORY,
        ranking_type=RankingType.INDEX,
        methodology_slug="devrankug-v1",
    )
    public_store.register_entity(
        EntityPublicRecord(
            id=ENTITY,
            slug="jane",
            name="Jane Doe",
            evidence_urls=["https://github.com/jane"],
        )
    )

    previous = PublishedRun(
        id=UUID(int=8), category_id=CATEGORY, quarter=Quarter(2026, 2),
        algorithm_name="DevRankUG", algorithm_version="1.0.0",
        status=RankingRunStatus.PUBLISHED,
        started_at=datetime(2026, 6, 30, tzinfo=UTC),
        published_at=datetime(2026, 6, 30, tzinfo=UTC),
    )
    current = PublishedRun(
        id=UUID(int=9), category_id=CATEGORY, quarter=Quarter(2026, 3),
        algorithm_name="DevRankUG", algorithm_version="1.0.0",
        status=RankingRunStatus.PUBLISHED,
        started_at=datetime(2026, 9, 30, tzinfo=UTC),
        published_at=datetime(2026, 9, 30, tzinfo=UTC),
    )
    previous_result = PublishedResult(
        id=UUID(int=43), ranking_run_id=previous.id, entity_id=ENTITY,
        rank=7, score=76.0, factor_breakdown={}, factor_coverage=1.0,
    )
    current_result = PublishedResult(
        id=UUID(int=44), ranking_run_id=current.id, entity_id=ENTITY,
        rank=3, score=88.5, factor_breakdown={}, factor_coverage=1.0, confidence=0.94,
    )
    public_store.ranking_store.runs.update({previous.id: previous, current.id: current})
    public_store.ranking_store.results.update({
        previous.id: (previous_result,),
        current.id: (current_result,),
    })
    public_store.ranking_store.official_by_category[CATEGORY] = current.id

    response = client.get(f"/v1/rankings/results/{current_result.id}/share?rank=999&score=999")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rank"] == 3
    assert payload["score"] == 88.5
    assert payload["movement"] == 4
    assert payload["entity_name"] == "Jane Doe"
    assert payload["canonical_url"].endswith("/people/jane")
    public_store.reset()
