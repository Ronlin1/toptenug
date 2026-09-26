from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.enums import EntityType, RankingRunStatus, ReviewStatus, UgandaRelation
from app.domain.models import Base, DerivedMetric, Entity, RankingResult, RankingRun
from app.operations import ROLLUP_VERSION, create_provisional_run, publish_quarter

METRICS = {
    "github.owned_repo_stars": 120.0,
    "github.contributions_90d": 80.0,
    "github.active_owned_repos_180d": 5.0,
    "github.followers": 90.0,
    "github.prs_and_reviews_90d": 40.0,
}


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_rankable_entity(session: Session) -> Entity:
    entity = Entity(
        slug="provisional-dev",
        name="Provisional Dev",
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
                quarter="2026-Q2",
                algorithm_version=ROLLUP_VERSION,
                provenance={"evidence_id": f"q2-{key}"},
            )
        )
        session.add(
            DerivedMetric(
                entity_id=entity.id,
                metric_key=key,
                value=value + 1,
                quarter="2026-Q3",
                algorithm_version=ROLLUP_VERSION,
                provenance={"evidence_id": f"q3-{key}"},
            )
        )
    session.commit()
    return entity


def test_provisional_run_is_new_and_never_mutates_published_run() -> None:
    with make_session() as session:
        seed_rankable_entity(session)
        official = publish_quarter(session, "github-developers", "2026-Q2")
        cutoff = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

        preview = create_provisional_run(session, "github-developers", "2026-Q3", cutoff)

        session.refresh(official)
        assert official.status is RankingRunStatus.PUBLISHED
        assert official.published_at is not None
        assert preview.id != official.id
        assert preview.status is RankingRunStatus.PROVISIONAL
        assert preview.published_at is None
        assert preview.cutoff_at == cutoff
        assert preview.candidate_count == 1
        assert preview.validation_details["official"] is False
        assert session.scalars(
            select(RankingResult).where(RankingResult.ranking_run_id == preview.id)
        ).all()


def test_new_provisional_run_does_not_mutate_previous_provisional_history() -> None:
    with make_session() as session:
        seed_rankable_entity(session)
        first = create_provisional_run(
            session,
            "github-developers",
            "2026-Q3",
            datetime(2026, 9, 25, 12, 0, tzinfo=UTC),
        )
        second = create_provisional_run(
            session,
            "github-developers",
            "2026-Q3",
            datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        )

        assert first.id != second.id
        assert first.status is RankingRunStatus.PROVISIONAL
        assert second.status is RankingRunStatus.PROVISIONAL
        assert session.scalars(select(RankingRun)).all().__len__() == 2
