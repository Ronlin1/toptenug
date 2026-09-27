from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api import sql_read
from app.api.store import public_store
from app.domain.enums import EntityType, EvidenceLevel, ReviewStatus, UgandaRelation
from app.domain.models import Base, Evidence, Observation, RankingResult, Source
from app.domain.schemas import CandidateProposal
from app.ingestion.candidates import approve_candidate, persist_candidate_proposals
from app.main import app
from app.operations import create_provisional_run, derive_quarter, publish_quarter
from app.quarterly.window import PublishWindowNotOpenError

METRICS = {
    "github.owned_repo_stars": 200,
    "github.contributions_90d": 80,
    "github.active_owned_repos_180d": 6,
    "github.followers": 120,
    "github.prs_and_reviews_90d": 45,
}


def _proposal(name: str, login: str) -> CandidateProposal:
    return CandidateProposal(
        display_name=name,
        entity_type=EntityType.PERSON,
        candidate_profiles={"github": f"https://github.com/{login}"},
        uganda_relation_claims=["Evidence-backed Ugandan developer"],
        source_urls=[f"https://example.com/evidence/{login}"],
        confidence=0.95,
        review_status=ReviewStatus.REVIEW_REQUIRED,
    )


def _add_github_observations(session: Session, entity_id, login: str, multiplier: int) -> None:
    source = session.scalar(select(Source).where(Source.key == "github"))
    assert source is not None
    observed_at = datetime(2026, 9, 27, 6, 0, tzinfo=UTC)
    for metric_key, base_value in METRICS.items():
        evidence_id = uuid5(NAMESPACE_URL, f"phase2:{login}:{metric_key}")
        session.add(
            Evidence(
                id=evidence_id,
                entity_id=entity_id,
                source_id=source.id,
                level=EvidenceLevel.A,
                source_url=f"https://github.com/{login}",
                retrieved_at=observed_at,
                claim=f"GitHub reported {metric_key}",
                confidence=1.0,
                review_status=ReviewStatus.APPROVED,
            )
        )
        session.add(
            Observation(
                entity_id=entity_id,
                source_id=source.id,
                evidence_id=evidence_id,
                source_record_id=f"{login}:{metric_key}:2026-Q3",
                metric_key=metric_key,
                raw_value=base_value * multiplier,
                observed_at=observed_at,
                retrieved_at=observed_at,
                source_url=f"https://github.com/{login}",
            )
        )
    session.commit()


def test_persisted_phase2_flow_keeps_preview_separate_and_publishes_only_after_cutoff(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        proposals = [_proposal("Alice Builder", "aliceug"), _proposal("Bob Builder", "bobug")]
        summary = persist_candidate_proposals(session, proposals, "fixture-grounded-search")
        assert summary.created == 2

        candidates = session.execute(select(__import__("app.domain.models", fromlist=["CandidateRecord"]).CandidateRecord)).scalars().all()
        entities = []
        for candidate in candidates:
            entity = approve_candidate(
                session,
                candidate.id,
                UgandaRelation.UGANDAN_IN_UGANDA,
                "Reviewed first-party/public evidence in fixture",
            )
            entities.append((entity, candidate.github_login))

        for index, (entity, login) in enumerate(entities, start=1):
            assert login is not None
            _add_github_observations(session, entity.id, login, index)

        derive_quarter(session, "2026-Q3")
        provisional = create_provisional_run(
            session,
            "github-developers",
            "2026-Q3",
            datetime(2026, 9, 27, 7, 0, tzinfo=UTC),
        )
        provisional_ids = list(
            session.scalars(
                select(RankingResult.id).where(RankingResult.ranking_run_id == provisional.id)
            ).all()
        )
        assert provisional_ids

        with pytest.raises(PublishWindowNotOpenError):
            publish_quarter(
                session,
                "github-developers",
                "2026-Q3",
                now=datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC),
            )

    @contextmanager
    def test_production_session():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(sql_read, "production_session", test_production_session)
    public_store.reset()
    client = TestClient(app)

    preview_response = client.get("/v1/preview/rankings/github-developers?limit=10&quarter=2026-Q3")
    assert preview_response.status_code == 200
    assert preview_response.json()["official"] is False
    assert preview_response.json()["results"]

    official_before = client.get("/v1/rankings/github-developers?limit=10&quarter=2026-Q3")
    assert official_before.status_code == 404
    provisional_share = client.get(f"/v1/rankings/results/{provisional_ids[0]}/share")
    assert provisional_share.status_code == 404

    with Session(engine) as session:
        published = publish_quarter(
            session,
            "github-developers",
            "2026-Q3",
            now=datetime(2026, 9, 30, 21, 0, 0, tzinfo=UTC),
        )
        published_result = session.scalar(
            select(RankingResult).where(RankingResult.ranking_run_id == published.id).order_by(RankingResult.rank)
        )
        assert published_result is not None
        published_result_id = published_result.id

    official_after = client.get("/v1/rankings/github-developers?limit=10&quarter=2026-Q3")
    assert official_after.status_code == 200
    payload = official_after.json()
    assert payload["algorithm_name"] == "DevRankUG"
    assert payload["algorithm_version"] == "1.0.0"
    assert len(payload["results"]) == 2

    top = payload["results"][0]
    assert client.get(f"/v1/entities/{top['entity_slug']}").status_code == 200
    assert client.get(f"/v1/entities/{top['entity_slug']}/history").status_code == 200
    share = client.get(f"/v1/rankings/results/{published_result_id}/share")
    assert share.status_code == 200
    assert share.json()["rank"] == top["rank"]
    public_store.reset()
