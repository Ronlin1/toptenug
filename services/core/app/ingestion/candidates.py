from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import EntityType, EvidenceLevel, ReviewStatus, UgandaRelation
from app.domain.models import CandidateRecord, Entity, Evidence, Source, SourceAccount
from app.domain.schemas import CandidateProposal

ALLOWED_UGANDAN_RELATIONS = {
    UgandaRelation.UGANDAN_IN_UGANDA,
    UgandaRelation.UGANDAN_DIASPORA,
}


@dataclass(frozen=True)
class CandidatePersistSummary:
    proposals: int
    created: int
    updated: int
    deduplicated: int
    review_required: int


def _normalize_url(value: str) -> str:
    return value.strip().rstrip("/").casefold()


def _github_login(proposal: CandidateProposal) -> str | None:
    for key, value in proposal.candidate_profiles.items():
        candidate = value.strip()
        if "github" not in key.casefold() and "github.com" not in candidate.casefold():
            continue
        if "github.com" in candidate.casefold():
            parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
            login = parsed.path.strip("/").split("/", 1)[0]
        else:
            login = candidate.removeprefix("@").strip("/")
        if login:
            return login.casefold()
    return None


def _github_profile_url(login: str | None) -> str | None:
    return f"https://github.com/{login}" if login else None


def _first_party_profile(proposal: CandidateProposal) -> str | None:
    candidates = [
        value
        for key, value in proposal.candidate_profiles.items()
        if "github" not in key.casefold() and "github.com" not in value.casefold()
    ]
    if not candidates:
        return None
    return sorted(_normalize_url(value) for value in candidates)[0]


def candidate_identity_key(proposal: CandidateProposal) -> str:
    login = _github_login(proposal)
    if login:
        return f"github:{login}"
    profile = _first_party_profile(proposal)
    if profile:
        return f"profile:{profile}"
    if not proposal.source_urls:
        raise ValueError("grounded candidate proposals require at least one source URL")
    normalized_name = " ".join(proposal.display_name.casefold().split())
    source_material = "|".join(sorted(_normalize_url(url) for url in proposal.source_urls))
    digest = sha256(f"{normalized_name}|{source_material}".encode()).hexdigest()
    return f"fallback:{digest}"


def _merge_review_status(current: ReviewStatus, incoming: ReviewStatus) -> ReviewStatus:
    if current in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
        return current
    if ReviewStatus.REVIEW_REQUIRED in {current, incoming}:
        return ReviewStatus.REVIEW_REQUIRED
    return ReviewStatus.PENDING


def _merge_discovery_sources(current: str, incoming: str) -> str:
    values = {value.strip() for value in current.split(",") if value.strip()}
    values.add(incoming.strip())
    return ",".join(sorted(values))[:200]


def _flag_name_conflicts(session: Session, candidate: CandidateRecord) -> None:
    conflicts = session.scalars(
        select(CandidateRecord).where(
            func.lower(CandidateRecord.display_name) == candidate.display_name.casefold(),
            CandidateRecord.normalized_identity_key != candidate.normalized_identity_key,
        )
    ).all()
    if conflicts:
        candidate.review_status = ReviewStatus.REVIEW_REQUIRED
        for conflict in conflicts:
            if conflict.review_status not in {ReviewStatus.APPROVED, ReviewStatus.REJECTED}:
                conflict.review_status = ReviewStatus.REVIEW_REQUIRED


def persist_candidate_proposals(
    session: Session,
    proposals: list[CandidateProposal],
    discovery_source: str,
) -> CandidatePersistSummary:
    created = 0
    updated = 0
    deduplicated = 0
    touched_keys: set[str] = set()

    for proposal in proposals:
        if not proposal.source_urls:
            raise ValueError("grounded candidate proposals require at least one source URL")
        identity_key = candidate_identity_key(proposal)
        touched_keys.add(identity_key)
        existing = session.scalar(
            select(CandidateRecord).where(CandidateRecord.normalized_identity_key == identity_key)
        )
        login = _github_login(proposal)
        if existing is None:
            existing = CandidateRecord(
                normalized_identity_key=identity_key,
                display_name=proposal.display_name,
                github_login=login,
                github_profile_url=_github_profile_url(login),
                profile_map=dict(proposal.candidate_profiles),
                proposed_uganda_relation=None,
                confidence=proposal.confidence,
                source_urls=sorted(set(proposal.source_urls)),
                discovery_source=discovery_source,
                review_status=proposal.review_status,
            )
            session.add(existing)
            session.flush()
            _flag_name_conflicts(session, existing)
            created += 1
        else:
            deduplicated += 1
            changed = False
            merged_profiles = {**existing.profile_map, **proposal.candidate_profiles}
            merged_urls = sorted(set(existing.source_urls) | set(proposal.source_urls))
            merged_status = _merge_review_status(existing.review_status, proposal.review_status)
            merged_source = _merge_discovery_sources(existing.discovery_source, discovery_source)
            merged_confidence = max(existing.confidence, proposal.confidence)
            if merged_profiles != existing.profile_map:
                existing.profile_map = merged_profiles
                changed = True
            if merged_urls != existing.source_urls:
                existing.source_urls = merged_urls
                changed = True
            if merged_status != existing.review_status:
                existing.review_status = merged_status
                changed = True
            if merged_source != existing.discovery_source:
                existing.discovery_source = merged_source
                changed = True
            if merged_confidence != existing.confidence:
                existing.confidence = merged_confidence
                changed = True
            _flag_name_conflicts(session, existing)
            if changed:
                updated += 1

    session.flush()
    review_required = len(
        session.scalars(
            select(CandidateRecord.id).where(
                CandidateRecord.normalized_identity_key.in_(touched_keys),
                CandidateRecord.review_status == ReviewStatus.REVIEW_REQUIRED,
            )
        ).all()
    )
    session.commit()
    return CandidatePersistSummary(
        proposals=len(proposals),
        created=created,
        updated=updated,
        deduplicated=deduplicated,
        review_required=review_required,
    )


def list_review_queue(session: Session, status: ReviewStatus) -> list[CandidateRecord]:
    return list(
        session.scalars(
            select(CandidateRecord)
            .where(CandidateRecord.review_status == status)
            .order_by(CandidateRecord.discovered_at, CandidateRecord.id)
        ).all()
    )


def _slug_for_entity(session: Session, name: str) -> str:
    base = "-".join(part for part in "".join(c if c.isalnum() else " " for c in name.casefold()).split())
    base = base or "developer"
    slug = base
    counter = 2
    while session.scalar(select(Entity.id).where(Entity.slug == slug)) is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def _github_source(session: Session) -> Source:
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
    return source


def approve_candidate(
    session: Session,
    candidate_id: UUID,
    relation: UgandaRelation,
    reviewer_note: str,
) -> Entity:
    if relation not in ALLOWED_UGANDAN_RELATIONS:
        raise ValueError("relation must be UGANDAN_IN_UGANDA or UGANDAN_DIASPORA")
    candidate = session.get(CandidateRecord, candidate_id)
    if candidate is None:
        raise ValueError(f"Candidate {candidate_id} was not found")
    if not candidate.source_urls:
        raise ValueError("candidate cannot be approved without grounded source URLs")

    entity = session.get(Entity, candidate.resolved_entity_id) if candidate.resolved_entity_id else None
    if entity is None:
        entity = Entity(
            slug=_slug_for_entity(session, candidate.display_name),
            name=candidate.display_name,
            entity_type=EntityType.PERSON,
        )
        session.add(entity)
        session.flush()

    entity.is_eligible = True
    entity.uganda_relation = relation
    entity.review_status = ReviewStatus.APPROVED
    candidate.proposed_uganda_relation = relation
    candidate.review_status = ReviewStatus.APPROVED
    candidate.resolved_entity_id = entity.id
    candidate.reviewer_note = reviewer_note

    for url in candidate.source_urls:
        evidence = session.scalar(
            select(Evidence).where(Evidence.entity_id == entity.id, Evidence.source_url == url)
        )
        if evidence is None:
            session.add(
                Evidence(
                    entity_id=entity.id,
                    source_id=None,
                    level=EvidenceLevel.D,
                    source_url=url,
                    retrieved_at=candidate.discovered_at,
                    claim=f"Reviewer-approved evidence for {relation.value}",
                    confidence=candidate.confidence,
                    review_status=ReviewStatus.APPROVED,
                )
            )
        else:
            evidence.review_status = ReviewStatus.APPROVED

    if candidate.github_login:
        source = _github_source(session)
        account = session.scalar(
            select(SourceAccount).where(
                SourceAccount.source_id == source.id,
                SourceAccount.external_id == candidate.github_login,
            )
        )
        if account is None:
            session.add(
                SourceAccount(
                    entity_id=entity.id,
                    source_id=source.id,
                    external_id=candidate.github_login,
                    canonical_url=candidate.github_profile_url or _github_profile_url(candidate.github_login) or "",
                )
            )
        elif account.entity_id != entity.id:
            raise ValueError("GitHub identity is already linked to another entity")

    session.commit()
    session.refresh(entity)
    return entity


def reject_candidate(session: Session, candidate_id: UUID, reviewer_note: str) -> CandidateRecord:
    candidate = session.get(CandidateRecord, candidate_id)
    if candidate is None:
        raise ValueError(f"Candidate {candidate_id} was not found")
    candidate.review_status = ReviewStatus.REJECTED
    candidate.reviewer_note = reviewer_note
    session.commit()
    session.refresh(candidate)
    return candidate
