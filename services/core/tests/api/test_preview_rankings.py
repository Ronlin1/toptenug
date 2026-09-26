from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.store import public_store
from app.domain.enums import EntityType, ReviewStatus, UgandaRelation
from app.domain.models import Base, DerivedMetric, Entity, RankingResult
from app.main import app
from app.operations import ROLLUP_VERSION, create_provisional_run

client = TestClient(app)
METRICS = {
    "github.owned_repo_stars": 120.0,
    "github.contributions_90d": 80.0,
    "github.active_owned_repos_180d": 5.0,
    "github.followers": 90.0,
    "github.prs_and_reviews_90d": 40.0,
}


@pytest.fixture()
def preview_db(monkeypatch: pytest.MonkeyPatch) -> tuple[sessionmaker[Session], str]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    public_store.reset()

    with factory() as session:
        entity = Entity(
            slug="preview-dev",
            name="Preview Dev",
            entity_type=EntityType.PERSON,
            is_eligible=True,
            uganda_relation=UgandaRelation.UGANDAN_IN_UGANDA,
            review_status=ReviewStatus.APPROVED,
        )
        session.add(entity)
        session.flush()
        for key, value in METRICS.items():
            session.add(
                DerivedMetric(
                    entity_id=entity.id,
                    metric_key=key,
                    value=value,
                    quarter="2026-Q3",
                    algorithm_version=ROLLUP_VERSION,
                    provenance={"evidence_id": f"preview-{key}"},
                )
            )
        session.commit()
        create_provisional_run(
            session,
            "github-developers",
            "2026-Q3",
            datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        )

    @contextmanager
    def fake_production_session() -> Iterator[Session]:
        with factory() as session:
            yield session

    monkeypatch.setattr("app.api.sql_read.production_session", fake_production_session)
    yield factory, "github-developers"
    public_store.reset()


@pytest.mark.parametrize("limit", [10, 20, 30, 50])
def test_preview_endpoint_returns_only_provisional_with_explicit_nonofficial_metadata(
    preview_db: tuple[sessionmaker[Session], str], limit: int
) -> None:
    _, slug = preview_db

    response = client.get(f"/v1/preview/rankings/{slug}?quarter=2026-Q3&limit={limit}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["official"] is False
    assert payload["quarter"] == "2026-Q3"
    assert payload["reviewed_pool_count"] == 1
    assert payload["cutoff_at"] == "2026-09-26T12:00:00"
    assert payload["limit"] == limit
    assert payload["results"][0]["rank"] == 1
    assert payload["results"][0]["ranking_result_id"]


def test_preview_limit_above_50_is_rejected(preview_db: tuple[sessionmaker[Session], str]) -> None:
    _, slug = preview_db
    assert client.get(f"/v1/preview/rankings/{slug}?quarter=2026-Q3&limit=51").status_code == 422


def test_official_endpoint_ignores_provisional_run(preview_db: tuple[sessionmaker[Session], str]) -> None:
    _, slug = preview_db
    response = client.get(f"/v1/rankings/{slug}?quarter=2026-Q3")
    assert response.status_code == 404


def test_official_share_endpoint_404s_for_provisional_result(
    preview_db: tuple[sessionmaker[Session], str]
) -> None:
    factory, _ = preview_db
    with factory() as session:
        result_id = session.scalar(select(RankingResult.id))
        assert result_id is not None

    response = client.get(f"/v1/rankings/results/{result_id}/share")
    assert response.status_code == 404
