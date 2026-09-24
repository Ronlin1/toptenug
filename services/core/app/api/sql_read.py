from __future__ import annotations
from contextlib import contextmanager
from typing import Any,Iterator
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import get_settings
from app.domain.enums import RankingRunStatus
from app.domain.models import AlgorithmDefinition,Entity,Evidence,RankingCategory,RankingResult,RankingRun
@contextmanager
def production_session()->Iterator[Session]:
    from app.db import SessionLocal
    with SessionLocal() as session:yield session
def _published_run(session:Session,category_id:UUID,quarter:str|None=None)->RankingRun|None:
    stmt=select(RankingRun).where(RankingRun.category_id==category_id,RankingRun.status==RankingRunStatus.PUBLISHED)
    if quarter is not None:stmt=stmt.where(RankingRun.quarter==quarter)
    return session.scalar(stmt.order_by(RankingRun.quarter.desc(),RankingRun.published_at.desc()))
def _previous_result(session:Session,run:RankingRun,eid:UUID)->RankingResult|None:
    prev=session.scalar(select(RankingRun).where(RankingRun.category_id==run.category_id,RankingRun.status==RankingRunStatus.PUBLISHED,RankingRun.quarter<run.quarter).order_by(RankingRun.quarter.desc()));return session.scalar(select(RankingResult).where(RankingResult.ranking_run_id==prev.id,RankingResult.entity_id==eid)) if prev else None
def ranking(session:Session,slug:str,limit:int,quarter:str|None)->dict[str,Any]|None:
    c=session.scalar(select(RankingCategory).where(RankingCategory.slug==slug))
    if c is None:return None
    run=_published_run(session,c.id,quarter)
    if run is None:return None
    alg=session.get(AlgorithmDefinition,run.algorithm_id);rows=session.scalars(select(RankingResult).where(RankingResult.ranking_run_id==run.id).order_by(RankingResult.rank).limit(limit)).all();out=[]
    for r in rows:
        e=session.get(Entity,r.entity_id);prev=_previous_result(session,run,r.entity_id);urls=list(session.scalars(select(Evidence.source_url).where(Evidence.entity_id==r.entity_id)).all());pr=prev.rank if prev else None;out.append({'ranking_result_id':str(r.id),'entity_id':str(r.entity_id),'entity_slug':e.slug if e else str(r.entity_id),'name':e.name if e else str(r.entity_id),'avatar_url':None,'rank':r.rank,'score':r.score,'previous_rank':pr,'movement':pr-r.rank if pr is not None else None,'confidence':r.confidence,'factor_coverage':float(r.provenance_summary.get('factor_coverage',1.0)),'factor_breakdown':r.factor_breakdown,'provenance':{'source_count':len(set(urls)),'source_urls':sorted(set(urls))},'profile_url':f'/v1/entities/{e.slug}' if e else None})
    name=alg.name if alg else 'Unknown';version=alg.version if alg else 'unknown';method='devrankug-v1' if name=='DevRankUG' else name.casefold();return {'slug':c.slug,'name':c.name,'quarter':run.quarter,'ranking_type':c.ranking_type.value,'algorithm_name':name,'algorithm_version':version,'published_at':run.published_at,'methodology_url':f'/v1/methodology/{method}','limit':limit,'results':out}
def entity(session:Session,slug:str)->dict[str,Any]|None:
    e=session.scalar(select(Entity).where(Entity.slug==slug))
    if e is None:return None
    urls=sorted(set(session.scalars(select(Evidence.source_url).where(Evidence.entity_id==e.id)).all()));ranks=[]
    for c in session.scalars(select(RankingCategory)).all():
        run=_published_run(session,c.id)
        if not run:continue
        r=session.scalar(select(RankingResult).where(RankingResult.ranking_run_id==run.id,RankingResult.entity_id==e.id))
        if not r:continue
        prev=_previous_result(session,run,e.id);alg=session.get(AlgorithmDefinition,run.algorithm_id);name=alg.name if alg else '';method='devrankug-v1' if name=='DevRankUG' else name.casefold();pr=prev.rank if prev else None;ranks.append({'ranking_result_id':str(r.id),'category_slug':c.slug,'category_name':c.name,'quarter':run.quarter,'rank':r.rank,'score':r.score,'previous_rank':pr,'movement':pr-r.rank if pr is not None else None,'confidence':r.confidence,'factor_coverage':float(r.provenance_summary.get('factor_coverage',1.0)),'factor_breakdown':r.factor_breakdown,'methodology_url':f'/v1/methodology/{method}'})
    return {'id':str(e.id),'slug':e.slug,'name':e.name,'avatar_url':None,'summary':None,'evidence_urls':urls,'current_rankings':ranks}
def history(session:Session,slug:str)->dict[str,Any]|None:
    e=session.scalar(select(Entity).where(Entity.slug==slug))
    if e is None:return None
    h=[]
    for run in session.scalars(select(RankingRun).where(RankingRun.status==RankingRunStatus.PUBLISHED).order_by(RankingRun.quarter.desc())).all():
        r=session.scalar(select(RankingResult).where(RankingResult.ranking_run_id==run.id,RankingResult.entity_id==e.id));c=session.get(RankingCategory,run.category_id)
        if r and c:h.append({'quarter':run.quarter,'category_slug':c.slug,'rank':r.rank,'score':r.score,'factor_coverage':float(r.provenance_summary.get('factor_coverage',1.0))})
    return {'entity_slug':slug,'history':h}
def methodology(session:Session,slug:str)->dict[str,Any]|None:
    if slug!='devrankug-v1':return None
    alg=session.scalar(select(AlgorithmDefinition).where(AlgorithmDefinition.name=='DevRankUG').order_by(AlgorithmDefinition.version.desc()))
    if not alg:return None
    s=alg.spec;return {'slug':slug,'name':alg.name,'version':alg.version,'ranking_type':alg.ranking_type.value,'eligibility_policy':s.get('eligibility_policy',''),'missing_data_policy':s.get('missing_data_policy',''),'minimum_factor_coverage':s.get('minimum_factor_coverage',0),'tie_breaker':s.get('tie_breaker',''),'factors':s.get('factors',{}),'limitations':['GitHub activity is not a universal measure of developer quality.','Private and non-GitHub work may be underrepresented.','Google/Gemini discovery and search order are not ranking factors.']}
def quarters(session:Session)->list[str]:return list(session.scalars(select(RankingRun.quarter).where(RankingRun.status==RankingRunStatus.PUBLISHED).distinct().order_by(RankingRun.quarter.desc())).all())
def dashboard(session:Session)->dict[str,Any]:
    qs=quarters(session);current=qs[0] if qs else None;entities=session.scalars(select(Entity)).all();cats=session.scalars(select(RankingCategory)).all();count=0
    if current:
        runs=session.scalars(select(RankingRun).where(RankingRun.status==RankingRunStatus.PUBLISHED,RankingRun.quarter==current)).all();count=sum(len(session.scalars(select(RankingResult).where(RankingResult.ranking_run_id==r.id)).all()) for r in runs)
    return {'current_quarter':current,'indexed_entities':len(entities),'active_rankings':len(cats),'published_results':count,'source_links':len(session.scalars(select(Evidence.id)).all()),'biggest_movers':[],'categories':[{'slug':c.slug,'name':c.name,'ranking_type':c.ranking_type.value} for c in cats]}
def share(session:Session,rid:UUID)->dict[str,Any]|None:
    r=session.get(RankingResult,rid)
    if not r:return None
    run=session.get(RankingRun,r.ranking_run_id)
    if not run or run.status!=RankingRunStatus.PUBLISHED:return None
    e=session.get(Entity,r.entity_id);c=session.get(RankingCategory,run.category_id);alg=session.get(AlgorithmDefinition,run.algorithm_id)
    if not e or not c or not alg:return None
    prev=_previous_result(session,run,e.id);pr=prev.rank if prev else None;base=get_settings().public_web_base_url.rstrip('/');return {'ranking_result_id':str(r.id),'rank':r.rank,'score':r.score,'movement':pr-r.rank if pr is not None else None,'entity_name':e.name,'entity_slug':e.slug,'category_name':c.name,'category_slug':c.slug,'ranking_type':c.ranking_type.value,'quarter':run.quarter,'algorithm_name':alg.name,'algorithm_version':alg.version,'canonical_url':f'{base}/people/{e.slug}','image_path':f'/api/share/{r.id}'}
