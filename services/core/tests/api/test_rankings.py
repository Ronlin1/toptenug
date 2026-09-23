from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.store import PublicRankingResult, PublicRankingRun, public_store
from app.domain.enums import RankingRunStatus, RankingType
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _seed_store():
    public_store.clear()
    public_store.add_run(PublicRankingRun(
        id=UUID(int=1), slug="github-developers", quarter="2026-Q3",
        ranking_type=RankingType.INDEX, algorithm_name="DevRankUG", algorithm_version="1.0.0",
        status=RankingRunStatus.PUBLISHED, published_at=datetime(2026, 9, 30, tzinfo=UTC),
        methodology_url="/v1/methodology/devrankug-v1",
        results=tuple(
            PublicRankingResult(entity_id=UUID(int=i), slug=f"person-{i}", name=f"Person {i}", rank=i, score=100-i, confidence=0.9)
            for i in range(1, 16)
        ),
    ))
    public_store.add_run(PublicRankingRun(
        id=UUID(int=2), slug="github-developers", quarter="2026-Q4",
        ranking_type=RankingType.INDEX, algorithm_name="DevRankUG", algorithm_version="1.0.0",
        status=RankingRunStatus.DRAFT, published_at=None,
        methodology_url="/v1/methodology/devrankug-v1", results=(),
    ))
    yield
    public_store.clear()


@pytest.mark.parametrize("limit", [10, 20, 30, 50])
def test_supported_public_limits(limit):
    response = client.get(f"/v1/rankings/github-developers?limit={limit}")
    assert response.status_code == 200
    assert len(response.json()["results"]) <= limit
    assert response.json()["quarter"] == "2026-Q3"


def test_limit_above_50_is_rejected():
    assert client.get("/v1/rankings/github-developers?limit=51").status_code == 422


def test_draft_runs_are_never_public():
    response = client.get("/v1/rankings/github-developers?quarter=2026-Q4")
    assert response.status_code == 404
