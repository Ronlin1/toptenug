from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.domain.enums import EntityType, EvidenceLevel, ReviewStatus, UgandaRelation
from app.domain.models import Base, Entity, IngestionRun, Observation, Source, SourceAccount
from app.domain.schemas import EntityRef, ObservationInput
from app.operations import ingest_github_batch
from app.sources.base import RetryableSourceError

OBSERVED_AT = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_entity(session: Session, login: str) -> Entity:
    source = session.scalar(select(Source).where(Source.key == "github"))
    if source is None:
        source = Source(
            key="github",
            name="GitHub",
            base_url="https://github.com",
            evidence_level=EvidenceLevel.A,
        )
        session.add(source)
        session.flush()
    entity = Entity(
        slug=login,
        name=login,
        entity_type=EntityType.PERSON,
        is_eligible=True,
        uganda_relation=UgandaRelation.UGANDAN_IN_UGANDA,
        review_status=ReviewStatus.APPROVED,
    )
    session.add(entity)
    session.flush()
    session.add(
        SourceAccount(
            entity_id=entity.id,
            source_id=source.id,
            external_id=login,
            canonical_url=f"https://github.com/{login}",
        )
    )
    session.commit()
    return entity


class FakeGitHubAdapter:
    def __init__(self, **_: object) -> None:
        pass

    async def collect(self, entity: EntityRef) -> list[ObservationInput]:
        if entity.external_id == "rate-limited":
            raise RetryableSourceError("rate limited", retry_after_seconds=60)
        source_url = f"https://github.com/{entity.external_id}"
        return [
            ObservationInput(
                metric_key="github.followers",
                raw_value=10,
                observed_at=OBSERVED_AT,
                source_url=source_url,
                evidence_id=uuid5(NAMESPACE_URL, f"{source_url}|followers"),
                source_record_id=f"{entity.external_id}:followers:2026-09-26",
            )
        ]


def test_batch_continues_after_retryable_failure_and_records_one_durable_run(monkeypatch) -> None:
    with make_session() as session:
        good = seed_entity(session, "good-dev")
        limited = seed_entity(session, "rate-limited")
        monkeypatch.setattr("app.operations.GitHubAdapter", FakeGitHubAdapter)

        result = asyncio.run(
            ingest_github_batch(session, [limited.id, good.id], continue_on_error=True)
        )

        assert result.attempted == 2
        assert result.succeeded == 1
        assert result.failed == 1
        assert result.observations_added == 1
        assert len(result.failures) == 1
        assert result.failures[0].entity_id == limited.id
        assert result.failures[0].retryable is True
        assert result.failures[0].retry_after_seconds == 60
        assert session.scalar(select(func.count()).select_from(Observation)) == 1

        runs = session.scalars(select(IngestionRun)).all()
        assert len(runs) == 1
        assert runs[0].status == "PARTIAL"
        assert runs[0].counts == {
            "attempted": 2,
            "succeeded": 1,
            "failed": 1,
            "observations_added": 1,
        }
        assert runs[0].failure_details is not None
        assert runs[0].failure_details["failures"][0]["entity_id"] == str(limited.id)
        assert not hasattr(runs[0], "rank")
        assert not hasattr(runs[0], "score")


def test_batch_rerun_is_idempotent_for_identical_source_observations(monkeypatch) -> None:
    with make_session() as session:
        entity = seed_entity(session, "stable-dev")
        monkeypatch.setattr("app.operations.GitHubAdapter", FakeGitHubAdapter)

        first = asyncio.run(ingest_github_batch(session, [entity.id]))
        second = asyncio.run(ingest_github_batch(session, [entity.id]))

        assert first.observations_added == 1
        assert second.observations_added == 0
        assert session.scalar(select(func.count()).select_from(Observation)) == 1
        assert len(session.scalars(select(IngestionRun)).all()) == 2


def test_batch_failure_preserves_prior_observations(monkeypatch) -> None:
    with make_session() as session:
        entity = seed_entity(session, "rate-limited")
        source = session.scalar(select(Source).where(Source.key == "github"))
        assert source is not None

        # First collect successfully with a non-failing login, then change only the
        # external identity used for the next source call. Historical observations
        # must remain untouched by that later failure.
        account = session.scalar(select(SourceAccount).where(SourceAccount.entity_id == entity.id))
        assert account is not None
        account.external_id = "good-before-limit"
        session.commit()
        monkeypatch.setattr("app.operations.GitHubAdapter", FakeGitHubAdapter)
        asyncio.run(ingest_github_batch(session, [entity.id]))
        assert session.scalar(select(func.count()).select_from(Observation)) == 1

        account.external_id = "rate-limited"
        session.commit()
        result = asyncio.run(ingest_github_batch(session, [entity.id]))

        assert result.failed == 1
        assert result.observations_added == 0
        assert session.scalar(select(func.count()).select_from(Observation)) == 1
