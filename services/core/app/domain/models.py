from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .enums import EntityType, EvidenceLevel, RankingRunStatus, RankingType, ReviewStatus, UgandaRelation


class Base(DeclarativeBase):
    pass


class UUIDMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class Entity(UUIDMixin, Base):
    __tablename__ = "entities"
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType))
    is_discoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    uganda_relation: Mapped[UgandaRelation | None] = mapped_column(Enum(UgandaRelation), nullable=True)
    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EntityAlias(UUIDMixin, Base):
    __tablename__ = "entity_aliases"
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint("entity_id", "alias", name="uq_entity_alias"),)


class Source(UUIDMixin, Base):
    __tablename__ = "sources"
    key: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    evidence_level: Mapped[EvidenceLevel] = mapped_column(Enum(EvidenceLevel))
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)


class SourceAccount(UUIDMixin, Base):
    __tablename__ = "source_accounts"
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    profile_url: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_source_external_id"),)


class Evidence(UUIDMixin, Base):
    __tablename__ = "evidence"
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    entity_id: Mapped[UUID | None] = mapped_column(ForeignKey("entities.id"), nullable=True, index=True)
    level: Mapped[EvidenceLevel] = mapped_column(Enum(EvidenceLevel))
    source_url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    claim: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    __table_args__ = (CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_evidence_confidence"),)


class Observation(UUIDMixin, Base):
    __tablename__ = "observations"
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    evidence_id: Mapped[UUID] = mapped_column(ForeignKey("evidence.id"), index=True)
    source_record_id: Mapped[str] = mapped_column(String(255))
    metric_key: Mapped[str] = mapped_column(String(255), index=True)
    raw_value: Mapped[Any] = mapped_column(JSON)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("source_id", "source_record_id", "metric_key", "observed_at", name="uq_observation_source_metric_time"),)


class MetricDefinition(UUIDMixin, Base):
    __tablename__ = "metric_definitions"
    key: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class DerivedMetric(UUIDMixin, Base):
    __tablename__ = "derived_metrics"
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    metric_definition_id: Mapped[UUID] = mapped_column(ForeignKey("metric_definitions.id"), index=True)
    quarter: Mapped[str] = mapped_column(String(7), index=True)
    value: Mapped[float] = mapped_column(Float)
    calculation_version: Mapped[str] = mapped_column(String(50))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("entity_id", "metric_definition_id", "quarter", "calculation_version", name="uq_derived_metric_version"),)


class RankingCategory(UUIDMixin, Base):
    __tablename__ = "ranking_categories"
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    ranking_type: Mapped[RankingType] = mapped_column(Enum(RankingType))
    eligibility_policy: Mapped[str] = mapped_column(String(255))


class AlgorithmDefinition(UUIDMixin, Base):
    __tablename__ = "algorithm_definitions"
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(50))
    ranking_type: Mapped[RankingType] = mapped_column(Enum(RankingType))
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("name", "version", name="uq_algorithm_name_version"),)


class RankingRun(UUIDMixin, Base):
    __tablename__ = "ranking_runs"
    category_id: Mapped[UUID] = mapped_column(ForeignKey("ranking_categories.id"), index=True)
    algorithm_id: Mapped[UUID] = mapped_column(ForeignKey("algorithm_definitions.id"), index=True)
    quarter: Mapped[str] = mapped_column(String(7), index=True)
    status: Mapped[RankingRunStatus] = mapped_column(Enum(RankingRunStatus), default=RankingRunStatus.DRAFT)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RankingResult(UUIDMixin, Base):
    __tablename__ = "ranking_results"
    ranking_run_id: Mapped[UUID] = mapped_column(ForeignKey("ranking_runs.id", ondelete="CASCADE"), index=True)
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entities.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)
    previous_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    movement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    factor_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    __table_args__ = (
        UniqueConstraint("ranking_run_id", "entity_id", name="uq_ranking_run_entity"),
        UniqueConstraint("ranking_run_id", "rank", name="uq_ranking_run_rank"),
        CheckConstraint("rank >= 1", name="ck_rank_positive"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_ranking_confidence"),
    )


class IngestionRun(UUIDMixin, Base):
    __tablename__ = "ingestion_runs"
    source_id: Mapped[UUID | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    counts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    failure: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
