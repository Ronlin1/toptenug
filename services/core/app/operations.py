from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC,datetime
from pathlib import Path
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.domain.enums import EvidenceLevel,RankingRunStatus,RankingType
from app.domain.models import AlgorithmDefinition,DerivedMetric,Entity,Evidence,Observation,RankingCategory,RankingResult,RankingRun,Source,SourceAccount
from app.domain.schemas import EntityRef
from app.quarterly.validate import QuarterValidator,ValidationInput,ValidationReport
from app.ranking.engine import CandidateMetrics,RankingEngine,ScoredCandidate
from app.ranking.loader import AlgorithmSpec,load_algorithm_spec
from app.sources.github import GitHubAdapter
ROLLUP_VERSION='observation-rollup-v1'
CATEGORY_ALGORITHMS={'github-developers':('DevRankUG','1.0.0',RankingType.INDEX)}
def _quarter_parts(v:str)->tuple[int,int]:
    if len(v)!=7 or v[4:6]!='-Q' or not v[:4].isdigit() or v[6] not in '1234':raise ValueError('quarter must use YYYY-QN where N is 1..4')
    return int(v[:4]),int(v[6])
def _quarter_end_exclusive(v:str)->datetime:
    y,q=_quarter_parts(v); return datetime(y+1,1,1,tzinfo=UTC) if q==4 else datetime(y,q*3+1,1,tzinfo=UTC)
def _previous_quarter(v:str)->str:
    y,q=_quarter_parts(v); return f'{y-1}-Q4' if q==1 else f'{y}-Q{q-1}'
def _algorithm_path(name:str,version:str)->Path:
    if (name,version)==('DevRankUG','1.0.0'):return Path(__file__).resolve().parent.parent/'algorithms'/'devrankug'/'v1.0.0.yaml'
    raise ValueError(f'No local algorithm specification registered for {name} {version}')
def ensure_category_and_algorithm(session:Session,slug:str)->tuple[RankingCategory,AlgorithmDefinition,AlgorithmSpec]:
    try:name,version,rtype=CATEGORY_ALGORITHMS[slug]
    except KeyError as exc:raise ValueError(f'Unsupported ranking category: {slug}') from exc
    spec=load_algorithm_spec(_algorithm_path(name,version)); c=session.scalar(select(RankingCategory).where(RankingCategory.slug==slug))
    if c is None:c=RankingCategory(slug=slug,name='GitHub Developers',ranking_type=rtype,eligibility_policy=spec.eligibility_policy); session.add(c); session.flush()
    a=session.scalar(select(AlgorithmDefinition).where(AlgorithmDefinition.name==name,AlgorithmDefinition.version==version))
    if a is None:a=AlgorithmDefinition(name=name,version=version,ranking_type=rtype,spec=spec.model_dump(mode='json')); session.add(a); session.flush()
    return c,a,spec
def _ensure_github_source(session:Session)->Source:
    s=session.scalar(select(Source).where(Source.key=='github'))
    if s is None:s=Source(key='github',name='GitHub',base_url='https://github.com',evidence_level=EvidenceLevel.A); session.add(s); session.flush()
    return s
def github_login_for_entity(session:Session,eid:UUID)->str:
    s=_ensure_github_source(session); a=session.scalar(select(SourceAccount).where(SourceAccount.entity_id==eid,SourceAccount.source_id==s.id))
    if a is None:raise ValueError(f'Entity {eid} has no verified GitHub source account.')
    return a.external_id
async def ingest_github_entity(session:Session,eid:UUID)->int:
    settings=get_settings(); source=_ensure_github_source(session); login=github_login_for_entity(session,eid); rows=await GitHubAdapter(token=settings.github_token,api_base_url=settings.github_api_base_url).collect(EntityRef(id=eid,external_id=login)); inserted=0
    for row in rows:
        if session.get(Evidence,row.evidence_id) is None:session.add(Evidence(id=row.evidence_id,entity_id=eid,source_id=source.id,level=EvidenceLevel.A,source_url=row.source_url,retrieved_at=datetime.now(UTC),claim=f'GitHub reported {row.metric_key}={row.raw_value}',confidence=1.0))
        rec=row.source_record_id or str(row.evidence_id); existing=session.scalar(select(Observation).where(Observation.source_id==source.id,Observation.source_record_id==rec,Observation.metric_key==row.metric_key,Observation.observed_at==row.observed_at))
        if existing:continue
        session.add(Observation(entity_id=eid,source_id=source.id,evidence_id=row.evidence_id,source_record_id=rec,metric_key=row.metric_key,raw_value=row.raw_value,observed_at=row.observed_at,retrieved_at=datetime.now(UTC),source_url=row.source_url)); inserted+=1
    session.commit(); return inserted
def derive_quarter(session:Session,quarter:str)->int:
    changed=0
    for entity in session.scalars(select(Entity).where(Entity.is_eligible.is_(True))).all():
        rows=session.scalars(select(Observation).where(Observation.entity_id==entity.id,Observation.observed_at<_quarter_end_exclusive(quarter)).order_by(Observation.observed_at.desc())).all(); latest={}
        for r in rows:latest.setdefault(r.metric_key,r)
        for key,r in latest.items():
            if isinstance(r.raw_value,bool) or not isinstance(r.raw_value,(int,float)):continue
            cur=session.scalar(select(DerivedMetric).where(DerivedMetric.entity_id==entity.id,DerivedMetric.metric_key==key,DerivedMetric.quarter==quarter,DerivedMetric.algorithm_version==ROLLUP_VERSION)); prov={'observation_id':str(r.id),'evidence_id':str(r.evidence_id),'source_url':r.source_url,'observed_at':r.observed_at.isoformat()}
            if cur is None:session.add(DerivedMetric(entity_id=entity.id,metric_key=key,value=float(r.raw_value),quarter=quarter,algorithm_version=ROLLUP_VERSION,provenance=prov))
            else:cur.value=float(r.raw_value); cur.provenance=prov; cur.computed_at=datetime.now(UTC)
            changed+=1
    session.commit(); return changed
def _candidate_metrics(session:Session,quarter:str)->tuple[list[CandidateMetrics],bool,list[tuple[str,float,float]]]:
    rows=session.scalars(select(DerivedMetric).where(DerivedMetric.quarter==quarter,DerivedMetric.algorithm_version==ROLLUP_VERSION)).all(); vals=defaultdict(dict); complete=True
    for r in rows:vals[r.entity_id][r.metric_key]=r.value; complete=complete and bool(r.provenance.get('evidence_id'))
    ids=list(vals); eligible={}
    if ids:eligible={e.id:e.is_eligible for e in session.scalars(select(Entity).where(Entity.id.in_(ids))).all()}
    candidates=[CandidateMetrics(eid,m,eligible.get(eid,False)) for eid,m in vals.items()]
    prev_rows=session.scalars(select(DerivedMetric).where(DerivedMetric.quarter==_previous_quarter(quarter),DerivedMetric.algorithm_version==ROLLUP_VERSION)).all(); prev={(r.entity_id,r.metric_key):r.value for r in prev_rows}; pairs=[(f'{r.entity_id}:{r.metric_key}',prev[(r.entity_id,r.metric_key)],r.value) for r in rows if (r.entity_id,r.metric_key) in prev]
    return candidates,complete,pairs
@dataclass(frozen=True)
class SnapshotEvaluation: category:RankingCategory; algorithm:AlgorithmDefinition; spec:AlgorithmSpec; rows:list[ScoredCandidate]; report:ValidationReport
def evaluate_snapshot(session:Session,slug:str,quarter:str)->SnapshotEvaluation:
    c,a,spec=ensure_category_and_algorithm(session,slug); candidates,complete,pairs=_candidate_metrics(session,quarter); raw=RankingEngine().run(spec,candidates); rows=[r for r in raw if r.qualified]; rows.sort(key=lambda r:(-r.score,str(r.entity_id))); rows=[ScoredCandidate(r.entity_id,r.score,i,r.factor_breakdown,r.factor_coverage,True) for i,r in enumerate(rows,1)]; report=QuarterValidator().validate(ValidationInput(complete,False,a.version,spec.version,[r.rank for r in rows],[r.factor_coverage for r in rows],pairs,spec.minimum_factor_coverage))
    if not rows:report=ValidationReport(errors=report.errors+('no_qualified_candidates',),blocking_anomalies=report.blocking_anomalies)
    return SnapshotEvaluation(c,a,spec,rows,report)
def validate_quarter(session:Session,slug:str,quarter:str)->ValidationReport:return evaluate_snapshot(session,slug,quarter).report
def publish_quarter(session:Session,slug:str,quarter:str)->RankingRun:
    e=evaluate_snapshot(session,slug,quarter); run=RankingRun(category_id=e.category.id,algorithm_id=e.algorithm.id,quarter=quarter,status=RankingRunStatus.DRAFT,started_at=datetime.now(UTC)); session.add(run); session.flush(); run.status=RankingRunStatus.VALIDATING
    if not e.report.ok:run.status=RankingRunStatus.FAILED; run.failure_details={'errors':list(e.report.errors),'blocking_anomalies':list(e.report.blocking_anomalies)}; session.commit(); raise ValueError(f'Quarter validation failed: {run.failure_details}')
    for r in e.rows:session.add(RankingResult(ranking_run_id=run.id,entity_id=r.entity_id,score=r.score,rank=r.rank,confidence=1.0,factor_breakdown={k:{'raw_value':v.raw_value,'normalized_value':v.normalized_value,'weight':v.weight,'contribution':v.contribution,'missing_policy':v.missing_policy} for k,v in r.factor_breakdown.items()},provenance_summary={'quarter':quarter,'rollup_version':ROLLUP_VERSION}))
    run.status=RankingRunStatus.PUBLISHED; run.published_at=datetime.now(UTC); session.commit(); return run
