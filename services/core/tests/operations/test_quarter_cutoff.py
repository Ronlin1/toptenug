from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.enums import EntityType, EvidenceLevel, ReviewStatus, UgandaRelation
from app.domain.models import Base, DerivedMetric, Entity, Evidence, Observation, Source
from app.operations import derive_quarter, publish_quarter
from app.quarterly.window import PublishWindowNotOpenError


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _eligible_entity(session: Session) -> tuple[Entity, Source, Evidence]:
    entity = Entity(
        slug="cutoff-dev",
        name="Cutoff Dev",
        entity_type=EntityType.PERSON,
        is_eligible=True,
        uganda_relation=UgandaRelation.UGANDAN_IN_UGANDA,
        review_status=ReviewStatus.APPROVED,
    )
    source = Source(
        key="github",
        name="GitHub",
        base_url="https://github.com",
        evidence_level=EvidenceLevel.A,
    )
    session.add_all([entity, source])
    session.flush()
    evidence = Evidence(
        entity_id=entity.id,
        source_id=source.id,
        level=EvidenceLevel.A,
        source_url="https://github.com/cutoff-dev",
        retrieved_at=datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC),
        claim="GitHub metric evidence",
        confidence=1.0,
        review_status=ReviewStatus.APPROVED,
    )
    session.add(evidence)
    session.flush()
    return entity, source, evidence


def _observation(
    session: Session,
    *,
    entity: Entity,
    source: Source,
    evidence: Evidence,
    value: int,
    observed_at: datetime,
    retrieved_at: datetime,
    record_id: str,
) -> Observation:
    row = Observation(
        entity_id=entity.id,
        source_id=source.id,
        evidence_id=evidence.id,
        source_record_id=record_id,
        metric_key="github.followers",
        raw_value=value,
        observed_at=observed_at,
        retrieved_at=retrieved_at,
        source_url="https://github.com/cutoff-dev",
    )
    session.add(row)
    session.flush()
    return row


def test_derive_q3_excludes_observation_at_exact_q4_boundary() -> None:
    with _session() as session:
        entity, source, evidence = _eligible_entity(session)
        eligible = _observation(
            session,
            entity=entity,
            source=source,
            evidence=evidence,
            value=10,
            observed_at=datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC),
            retrieved_at=datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC),
            record_id="eligible",
        )
        _observation(
            session,
            entity=entity,
            source=source,
            evidence=evidence,
            value=999,
            observed_at=datetime(2026, 9, 30, 21, 0, 0, tzinfo=UTC),
            retrieved_at=datetime(2026, 9, 30, 21, 0, 0, tzinfo=UTC),
            record_id="q4",
        )
        session.commit()

        derive_quarter(session, "2026-Q3")

        derived = session.scalar(
            select(DerivedMetric).where(
                DerivedMetric.entity_id == entity.id,
                DerivedMetric.metric_key == "github.followers",
                DerivedMetric.quarter == "2026-Q3",
            )
        )
        assert derived is not None
        assert derived.value == 10
        assert derived.provenance["observation_id"] == str(eligible.id)


def test_late_retrieval_preserves_source_observation_time_in_provenance() -> None:
    with _session() as session:
        entity, source, evidence = _eligible_entity(session)
        observed_at = datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC)
        retrieved_at = datetime(2026, 10, 1, 8, 0, 0, tzinfo=UTC)
        row = _observation(
            session,
            entity=entity,
            source=source,
            evidence=evidence,
            value=25,
            observed_at=observed_at,
            retrieved_at=retrieved_at,
            record_id="late-verification",
        )
        session.commit()

        derive_quarter(session, "2026-Q3")

        session.refresh(row)
        derived = session.scalar(
            select(DerivedMetric).where(
                DerivedMetric.entity_id == entity.id,
                DerivedMetric.metric_key == "github.followers",
                DerivedMetric.quarter == "2026-Q3",
            )
        )
        assert row.observed_at == observed_at
        assert derived is not None
        assert derived.provenance["observed_at"] == observed_at.isoformat()
        assert derived.provenance["retrieved_at"] == retrieved_at.isoformat()


def test_publish_quarter_rejects_clock_before_q3_cutoff() -> None:
    with _session() as session:
        with pytest.raises(PublishWindowNotOpenError):
            publish_quarter(
                session,
                "github-developers",
                "2026-Q3",
                now=datetime(2026, 9, 30, 20, 59, 59, tzinfo=UTC),
            )
