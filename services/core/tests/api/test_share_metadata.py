from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.store import PublicRankingResult, PublicRankingRun, public_store
from app.domain.enums import RankingRunStatus, RankingType
from app.main import app

client = TestClient(app)


def test_share_metadata_comes_from_published_result():
    public_store.clear()
    result = PublicRankingResult(
        id=UUID(int=44), entity_id=UUID(int=7), slug="jane", name="Jane Doe",
        rank=3, score=88.5, confidence=.94, previous_rank=7,
        evidence_urls=("https://github.com/jane",),
    )
    public_store.add_run(PublicRankingRun(
        id=UUID(int=9), slug="github-developers", quarter="2026-Q3",
        ranking_type=RankingType.INDEX, algorithm_name="DevRankUG", algorithm_version="1.0.0",
        status=RankingRunStatus.PUBLISHED, published_at=datetime(2026,9,30,tzinfo=UTC),
        methodology_url="/v1/methodology/devrankug-v1", results=(result,),
    ))
    payload = client.get(f"/v1/rankings/results/{result.id}/share").json()
    assert payload["rank"] == result.rank
    assert payload["score"] == result.score
    assert payload["movement"] == 4
    assert payload["canonical_url"].endswith("/people/jane")
    public_store.clear()
