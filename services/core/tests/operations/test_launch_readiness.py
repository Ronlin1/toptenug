from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.enums import EntityType, RankingRunStatus, ReviewStatus, UgandaRelation
from app.domain.models import Base, CandidateRecord, Entity, IngestionRun, RankingRun, SourceAccount
from app.quarterly.validate import ValidationReport
from app.readiness import launch_readiness


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _candidate(index: int, *, status: ReviewStatus = ReviewStatus.PENDING) -> CandidateRecord:
    return CandidateRecord(
        normalized_identity_key=f"github:candidate-{index}",
        display_name=f"Candidate {index}",
        github_login=f"candidate-{index}",
        github_profile_url=f"https://github.com/candidate-{index}",
        profile_map={"github": f"candidate-{index}"},
        confidence=0.95,
        source_urls=[f"https://example.com/candidate-{index}"],
        discovery_source="fixture",
        review_status=status,
    )


def _seed_candidates(session: Session, *, discovered: int, eligible: int) -> None:
    candidates = [_candidate(index) for index in range(discovered)]
    session.add_all(candidates)
    session.flush()
    for index, candidate in enumerate(candidates[:eligible]):
        candidate.review_status = ReviewStatus.APPROVED
        entity = Entity(
            slug=f"candidate-{index}",
            name=candidate.display_name,
            entity_type=EntityType.PERSON,
            is_eligible=True,
            uganda_relation=UgandaRelation.UGANDAN_IN_UGANDA,
            review_status=ReviewStatus.APPROVED,
        )
        session.add(entity)
        session.flush()
        candidate.resolved_entity_id = entity.id
        session.add(
            SourceAccount(
                entity_id=entity.id,
                source_id=uuid4(),
                external_id=f"candidate-{index}",
                canonical_url=f"https://github.com/candidate-{index}",
            )
        )
    session.commit()


def _evaluation(*, qualified: int, blocking_anomalies: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        category=SimpleNamespace(id=uuid4()),
        rows=[SimpleNamespace(rank=index + 1) for index in range(qualified)],
        report=ValidationReport(
            errors=(),
            blocking_anomalies=tuple(f"anomaly-{index}" for index in range(blocking_anomalies)),
        ),
    )


def test_national_release_requires_100_discovered_50_eligible_and_50_qualified(monkeypatch) -> None:
    with _session() as session:
        _seed_candidates(session, discovered=99, eligible=49)
        monkeypatch.setattr("app.readiness.evaluate_snapshot", lambda *_: _evaluation(qualified=49))

        report = launch_readiness(session, "github-developers", "2026-Q3")

        assert not report.ready_for_national_release
        assert "discovered_below_100" in report.blockers
        assert "eligible_below_50" in report.blockers
        assert "qualified_below_50" in report.blockers


def test_national_release_is_ready_only_when_every_gate_is_clear(monkeypatch) -> None:
    with _session() as session:
        _seed_candidates(session, discovered=100, eligible=50)
        monkeypatch.setattr("app.readiness.evaluate_snapshot", lambda *_: _evaluation(qualified=50))

        report = launch_readiness(session, "github-developers", "2026-Q3")

        assert report.discovered == 100
        assert report.eligible == 50
        assert report.github_resolved == 50
        assert report.qualified == 50
        assert report.unresolved_duplicates == 0
        assert report.blocking_anomalies == 0
        assert report.source_failures == 0
        assert report.ready_for_national_release
        assert report.blockers == ()


def test_duplicate_conflicts_and_source_failures_block_release(monkeypatch) -> None:
    with _session() as session:
        _seed_candidates(session, discovered=100, eligible=50)
        first = session.query(CandidateRecord).first()
        assert first is not None
        first.review_status = ReviewStatus.REVIEW_REQUIRED
        session.add(
            CandidateRecord(
                normalized_identity_key="github:conflicting-login",
                display_name=first.display_name,
                github_login="conflicting-login",
                github_profile_url="https://github.com/conflicting-login",
                profile_map={"github": "conflicting-login"},
                confidence=0.9,
                source_urls=["https://example.com/conflict"],
                discovery_source="fixture",
                review_status=ReviewStatus.REVIEW_REQUIRED,
            )
        )
        session.add(
            IngestionRun(
                source_key="github",
                status="PARTIAL",
                finished_at=datetime.now(UTC),
                counts={"attempted": 50, "succeeded": 49, "failed": 1},
            )
        )
        session.commit()
        monkeypatch.setattr("app.readiness.evaluate_snapshot", lambda *_: _evaluation(qualified=50))

        report = launch_readiness(session, "github-developers", "2026-Q3")

        assert report.unresolved_duplicates >= 1
        assert report.source_failures == 1
        assert not report.ready_for_national_release
        assert "unresolved_duplicates" in report.blockers
        assert "source_failures" in report.blockers


def test_small_reviewed_pool_can_be_preview_ready(monkeypatch) -> None:
    category_id = uuid4()
    with _session() as session:
        _seed_candidates(session, discovered=12, eligible=3)
        session.add(
            RankingRun(
                category_id=category_id,
                algorithm_id=uuid4(),
                quarter="2026-Q3",
                status=RankingRunStatus.PROVISIONAL,
                candidate_count=3,
                cutoff_at=datetime(2026, 9, 27, 5, 0, tzinfo=UTC),
                validation_details={"ranked_count": 3, "validation_ok": True},
            )
        )
        session.commit()
        evaluation = _evaluation(qualified=3)
        evaluation.category.id = category_id
        monkeypatch.setattr("app.readiness.evaluate_snapshot", lambda *_: evaluation)

        report = launch_readiness(session, "github-developers", "2026-Q3")

        assert report.preview_ready
        assert not report.ready_for_national_release
