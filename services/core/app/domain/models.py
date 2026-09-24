from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from .enums import EntityType,EvidenceLevel,RankingRunStatus,RankingType,ReviewStatus,UgandaRelation

def utcnow()->datetime: return datetime.now(UTC)
class Base(DeclarativeBase): pass
class Entity(Base):
    __tablename__="entities"
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); slug:Mapped[str]=mapped_column(String(250),unique=True,nullable=False); name:Mapped[str]=mapped_column(String(250),nullable=False); entity_type:Mapped[EntityType]=mapped_column(Enum(EntityType),nullable=False); is_discoverable:Mapped[bool]=mapped_column(Boolean,default=True,nullable=False); is_eligible:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False); uganda_relation:Mapped[UgandaRelation|None]=mapped_column(Enum(UgandaRelation)); review_status:Mapped[ReviewStatus]=mapped_column(Enum(ReviewStatus),default=ReviewStatus.PENDING,nullable=False); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class EntityAlias(Base):
    __tablename__="entity_aliases"; __table_args__=(UniqueConstraint("entity_id","alias",name="uq_entity_alias"),)
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); entity_id:Mapped[UUID]=mapped_column(ForeignKey("entities.id"),nullable=False); alias:Mapped[str]=mapped_column(String(250),nullable=False); source:Mapped[str|None]=mapped_column(String(100))
class Source(Base):
    __tablename__="sources"
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); key:Mapped[str]=mapped_column(String(100),unique=True,nullable=False); name:Mapped[str]=mapped_column(String(200),nullable=False); base_url:Mapped[str|None]=mapped_column(String(500)); evidence_level:Mapped[EvidenceLevel]=mapped_column(Enum(EvidenceLevel),nullable=False)
class SourceAccount(Base):
    __tablename__="source_accounts"; __table_args__=(UniqueConstraint("source_id","external_id",name="uq_source_account"),)
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); entity_id:Mapped[UUID]=mapped_column(ForeignKey("entities.id"),nullable=False); source_id:Mapped[UUID]=mapped_column(ForeignKey("sources.id"),nullable=False); external_id:Mapped[str]=mapped_column(String(250),nullable=False); canonical_url:Mapped[str]=mapped_column(String(1000),nullable=False)
class Evidence(Base):
    __tablename__="evidence"; __table_args__=(CheckConstraint("confidence >= 0 AND confidence <= 1",name="ck_evidence_conf"),)
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); entity_id:Mapped[UUID|None]=mapped_column(ForeignKey("entities.id")); source_id:Mapped[UUID|None]=mapped_column(ForeignKey("sources.id")); level:Mapped[EvidenceLevel]=mapped_column(Enum(EvidenceLevel),nullable=False); source_url:Mapped[str]=mapped_column(String(1500),nullable=False); retrieved_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); claim:Mapped[str]=mapped_column(Text,nullable=False); confidence:Mapped[float]=mapped_column(Float,nullable=False); content_hash:Mapped[str|None]=mapped_column(String(128)); review_status:Mapped[ReviewStatus]=mapped_column(Enum(ReviewStatus),default=ReviewStatus.PENDING,nullable=False)
class Observation(Base):
    __tablename__="observations"; __table_args__=(UniqueConstraint("source_id","source_record_id","metric_key","observed_at",name="uq_observation_source"),)
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); entity_id:Mapped[UUID]=mapped_column(ForeignKey("entities.id"),nullable=False); source_id:Mapped[UUID]=mapped_column(ForeignKey("sources.id"),nullable=False); evidence_id:Mapped[UUID]=mapped_column(ForeignKey("evidence.id"),nullable=False); source_record_id:Mapped[str]=mapped_column(String(300),nullable=False); metric_key:Mapped[str]=mapped_column(String(200),nullable=False); raw_value:Mapped[Any]=mapped_column(JSON,nullable=False); unit:Mapped[str|None]=mapped_column(String(50)); observed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); retrieved_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False); source_url:Mapped[str]=mapped_column(String(1500),nullable=False)
class MetricDefinition(Base):
    __tablename__="metric_definitions"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); key:Mapped[str]=mapped_column(String(200),unique=True,nullable=False); description:Mapped[str]=mapped_column(Text,nullable=False); unit:Mapped[str|None]=mapped_column(String(50))
class DerivedMetric(Base):
    __tablename__="derived_metrics"; __table_args__=(UniqueConstraint("entity_id","metric_key","quarter","algorithm_version",name="uq_derived_metric"),)
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); entity_id:Mapped[UUID]=mapped_column(ForeignKey("entities.id"),nullable=False); metric_key:Mapped[str]=mapped_column(String(200),nullable=False); value:Mapped[float]=mapped_column(Float,nullable=False); quarter:Mapped[str]=mapped_column(String(7),nullable=False); algorithm_version:Mapped[str]=mapped_column(String(50),nullable=False); provenance:Mapped[dict[str,Any]]=mapped_column(JSON,default=dict,nullable=False); computed_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow)
class RankingCategory(Base):
    __tablename__="ranking_categories"; id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); slug:Mapped[str]=mapped_column(String(200),unique=True,nullable=False); name:Mapped[str]=mapped_column(String(250),nullable=False); ranking_type:Mapped[RankingType]=mapped_column(Enum(RankingType),nullable=False); eligibility_policy:Mapped[str]=mapped_column(String(250),nullable=False)
class AlgorithmDefinition(Base):
    __tablename__="algorithm_definitions"; __table_args__=(UniqueConstraint("name","version",name="uq_algorithm_version"),)
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); name:Mapped[str]=mapped_column(String(200),nullable=False); version:Mapped[str]=mapped_column(String(50),nullable=False); ranking_type:Mapped[RankingType]=mapped_column(Enum(RankingType),nullable=False); spec:Mapped[dict[str,Any]]=mapped_column(JSON,nullable=False)
class RankingRun(Base):
    __tablename__="ranking_runs"
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); category_id:Mapped[UUID]=mapped_column(ForeignKey("ranking_categories.id"),nullable=False); algorithm_id:Mapped[UUID]=mapped_column(ForeignKey("algorithm_definitions.id"),nullable=False); quarter:Mapped[str]=mapped_column(String(7),nullable=False); status:Mapped[RankingRunStatus]=mapped_column(Enum(RankingRunStatus),default=RankingRunStatus.DRAFT,nullable=False); started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow); published_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); failure_details:Mapped[dict[str,Any]|None]=mapped_column(JSON)
class RankingResult(Base):
    __tablename__="ranking_results"; __table_args__=(UniqueConstraint("ranking_run_id","entity_id",name="uq_run_entity"),UniqueConstraint("ranking_run_id","rank",name="uq_run_rank"),CheckConstraint("rank >= 1",name="ck_rank_positive"),CheckConstraint("confidence >= 0 AND confidence <= 1",name="ck_rank_conf"))
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); ranking_run_id:Mapped[UUID]=mapped_column(ForeignKey("ranking_runs.id"),nullable=False); entity_id:Mapped[UUID]=mapped_column(ForeignKey("entities.id"),nullable=False); score:Mapped[float]=mapped_column(Float,nullable=False); rank:Mapped[int]=mapped_column(Integer,nullable=False); previous_rank:Mapped[int|None]=mapped_column(Integer); movement:Mapped[int|None]=mapped_column(Integer); confidence:Mapped[float]=mapped_column(Float,default=1.0,nullable=False); factor_breakdown:Mapped[dict[str,Any]]=mapped_column(JSON,default=dict,nullable=False); provenance_summary:Mapped[dict[str,Any]]=mapped_column(JSON,default=dict,nullable=False)
class IngestionRun(Base):
    __tablename__="ingestion_runs"
    id:Mapped[UUID]=mapped_column(Uuid,primary_key=True,default=uuid4); source_key:Mapped[str]=mapped_column(String(100),nullable=False); status:Mapped[str]=mapped_column(String(50),nullable=False); started_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow); finished_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); counts:Mapped[dict[str,Any]]=mapped_column(JSON,default=dict,nullable=False); failure_details:Mapped[dict[str,Any]|None]=mapped_column(JSON)
