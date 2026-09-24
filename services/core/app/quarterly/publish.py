from dataclasses import dataclass,field,replace
from datetime import UTC,datetime
from uuid import UUID,uuid4
from app.domain.enums import RankingRunStatus
from app.ranking.engine import CandidateMetrics,RankingEngine,ScoredCandidate
from app.ranking.loader import AlgorithmSpec
from .validate import QuarterValidator,ValidationInput
class QuarterValidationError(RuntimeError):pass
@dataclass(frozen=True,order=True)
class Quarter:
    year:int; quarter:int
    def __post_init__(self)->None:
        if self.quarter not in {1,2,3,4}:raise ValueError('quarter must be 1..4')
    def __str__(self)->str:return f'{self.year}-Q{self.quarter}'
@dataclass(frozen=True)
class CategorySnapshotInput:
    spec:AlgorithmSpec; candidates:list[CandidateMetrics]; provenance_complete:bool=True; stale_critical_sources:bool=False; metric_pairs:list[tuple[str,float,float]]=field(default_factory=list)
@dataclass(frozen=True)
class PublishedRun:
    id:UUID; category_id:UUID; quarter:Quarter; algorithm_name:str; algorithm_version:str; status:RankingRunStatus; started_at:datetime; published_at:datetime|None=None; failure_details:tuple[str,...]=()
@dataclass(frozen=True)
class PublishedResult:
    id:UUID; ranking_run_id:UUID; entity_id:UUID; rank:int; score:float; factor_breakdown:dict[str,object]; factor_coverage:float; confidence:float=1.0
class InMemoryRankingStore:
    def __init__(self)->None:self.category_inputs={}; self.runs={}; self.results={}; self.official_by_category={}
    def configure_category(self,cid:UUID,snapshot:CategorySnapshotInput)->None:self.category_inputs[cid]=snapshot
    def current_official(self,cid:UUID)->PublishedRun:return self.runs[self.official_by_category[cid]]
class QuarterPublisher:
    def __init__(self,store:InMemoryRankingStore,validator:QuarterValidator|None=None,engine:RankingEngine|None=None)->None:self.store=store; self.validator=validator or QuarterValidator(); self.engine=engine or RankingEngine()
    def preview(self,cid:UUID,version:str)->list[ScoredCandidate]:
        snap=self.store.category_inputs[cid]
        if snap.spec.version!=version:raise QuarterValidationError('algorithm_version_mismatch')
        q=[r for r in self.engine.run(snap.spec,snap.candidates) if r.qualified]; q=sorted(q,key=lambda r:(-r.score,str(r.entity_id))); return [replace(r,rank=i) for i,r in enumerate(q,1)]
    def publish(self,quarter:Quarter,cid:UUID,version:str)->PublishedRun:
        snap=self.store.category_inputs[cid]; rid=uuid4(); draft=PublishedRun(rid,cid,quarter,snap.spec.name,version,RankingRunStatus.DRAFT,datetime.now(UTC)); self.store.runs[rid]=draft; validating=replace(draft,status=RankingRunStatus.VALIDATING); self.store.runs[rid]=validating
        try:
            scored=self.preview(cid,version); report=self.validator.validate(ValidationInput(snap.provenance_complete,snap.stale_critical_sources,version,snap.spec.version,[r.rank for r in scored],[r.factor_coverage for r in scored],snap.metric_pairs,snap.spec.minimum_factor_coverage))
            if not scored:report=replace(report,errors=report.errors+('no_qualified_candidates',))
            if not report.ok:
                failed=replace(validating,status=RankingRunStatus.FAILED,failure_details=report.errors+report.blocking_anomalies); self.store.runs[rid]=failed; raise QuarterValidationError(','.join(failed.failure_details))
            results=tuple(PublishedResult(uuid4(),rid,r.entity_id,r.rank,r.score,{k:{'raw_value':v.raw_value,'normalized_value':v.normalized_value,'weight':v.weight,'contribution':v.contribution,'missing_policy':v.missing_policy} for k,v in r.factor_breakdown.items()},r.factor_coverage) for r in scored); published=replace(validating,status=RankingRunStatus.PUBLISHED,published_at=datetime.now(UTC)); self.store.results[rid]=results; self.store.runs[rid]=published; self.store.official_by_category[cid]=rid; return published
        except QuarterValidationError:raise
        except Exception as exc:self.store.runs[rid]=replace(validating,status=RankingRunStatus.FAILED,failure_details=(type(exc).__name__,str(exc))); raise
    def current_official(self,cid:UUID)->PublishedRun:return self.store.current_official(cid)
