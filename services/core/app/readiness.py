from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import RankingRunStatus, ReviewStatus, UgandaRelation
from app.domain.models import CandidateRecord, Entity, IngestionRun, RankingRun, Source, SourceAccount
from app.operations import evaluate_snapshot

OFFICIAL_PERSON_RELATIONS = {
    UgandaRelation.UGANDAN_IN_UGANDA,
    UgandaRelation.UGANDAN_DIASPORA,
}


@dataclass(frozen=True)
class LaunchReadinessReport:
    discovered: int
    reviewed: int
    eligible: int
    github_resolved: int
    qualified: int
    unresolved_duplicates: int
    blocking_anomalies: int
    source_failures: int
    preview_ready: bool
    ready_for_national_release: bool
    blockers: tuple[str, ...]


def _count(session: Session, statement: Any) -> int:
    return int(session.scalar(statement) or 0)


def _unresolved_duplicate_groups(session: Session) -> int:
    rows = session.scalars(
        select(CandidateRecord).where(CandidateRecord.review_status == ReviewStatus.REVIEW_REQUIRED)
    ).all()
    by_name: dict[str, set[str]] = {}
    for row in rows:
        name = " ".join(row.display_name.casefold().split())
        by_name.setdefault(name, set()).add(row.normalized_identity_key)
    return sum(1 for identities in by_name.values() if len(identities) > 1)


def _latest_github_failures(session: Session) -> int:
    latest = session.scalar(
        select(IngestionRun)
        .where(IngestionRun.source_key == "github")
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(1)
    )
    if latest is None:
        return 0
    failed = latest.counts.get("failed", 0)
    return int(failed) if isinstance(failed, (int, float)) and not isinstance(failed, bool) else 0


def _preview_run_is_valid(session: Session, category_id: object, quarter: str) -> bool:
    run = session.scalar(
        select(RankingRun)
        .where(
            RankingRun.category_id == category_id,
            RankingRun.quarter == quarter,
            RankingRun.status == RankingRunStatus.PROVISIONAL,
        )
        .order_by(RankingRun.started_at.desc(), RankingRun.id.desc())
        .limit(1)
    )
    if run is None:
        return False
    details = run.validation_details or {}
    ranked_count = details.get("ranked_count", 0)
    return bool(details.get("validation_ok")) and isinstance(ranked_count, int) and ranked_count > 0


def launch_readiness(session: Session, category: str, quarter: str) -> LaunchReadinessReport:
    evaluation = evaluate_snapshot(session, category, quarter)

    discovered = _count(session, select(func.count()).select_from(CandidateRecord))
    reviewed = _count(
        session,
        select(func.count())
        .select_from(CandidateRecord)
        .where(CandidateRecord.review_status.in_([ReviewStatus.APPROVED, ReviewStatus.REJECTED])),
    )
    eligible = _count(
        session,
        select(func.count())
        .select_from(Entity)
        .where(
            Entity.is_eligible.is_(True),
            Entity.review_status == ReviewStatus.APPROVED,
            Entity.uganda_relation.in_(OFFICIAL_PERSON_RELATIONS),
        ),
    )
    github_resolved = _count(
        session,
        select(func.count(func.distinct(Entity.id)))
        .select_from(Entity)
        .join(SourceAccount, SourceAccount.entity_id == Entity.id)
        .join(Source, Source.id == SourceAccount.source_id)
        .where(
            Entity.is_eligible.is_(True),
            Entity.review_status == ReviewStatus.APPROVED,
            Entity.uganda_relation.in_(OFFICIAL_PERSON_RELATIONS),
            Source.key == "github",
        ),
    )
    qualified = len(evaluation.rows)
    unresolved_duplicates = _unresolved_duplicate_groups(session)
    blocking_anomalies = len(evaluation.report.blocking_anomalies)
    source_failures = _latest_github_failures(session)
    validation_ok = evaluation.report.ok
    preview_ready = (
        eligible > 0
        and qualified > 0
        and validation_ok
        and _preview_run_is_valid(session, evaluation.category.id, quarter)
    )

    blockers: list[str] = []
    if discovered < 100:
        blockers.append("discovered_below_100")
    if eligible < 50:
        blockers.append("eligible_below_50")
    if github_resolved < 50:
        blockers.append("github_resolved_below_50")
    if qualified < 50:
        blockers.append("qualified_below_50")
    if unresolved_duplicates:
        blockers.append("unresolved_duplicates")
    if blocking_anomalies:
        blockers.append("blocking_anomalies")
    if source_failures:
        blockers.append("source_failures")
    if not validation_ok:
        blockers.append("ranking_validation_failed")

    return LaunchReadinessReport(
        discovered=discovered,
        reviewed=reviewed,
        eligible=eligible,
        github_resolved=github_resolved,
        qualified=qualified,
        unresolved_duplicates=unresolved_duplicates,
        blocking_anomalies=blocking_anomalies,
        source_failures=source_failures,
        preview_ready=preview_ready,
        ready_for_national_release=not blockers,
        blockers=tuple(blockers),
    )
