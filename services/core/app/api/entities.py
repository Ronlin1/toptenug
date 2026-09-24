from typing import Any
from fastapi import APIRouter,HTTPException
from app.domain.enums import RankingRunStatus
from .store import public_store
from . import sql_read
router=APIRouter(prefix='/v1/entities',tags=['entities'])
@router.get('/{slug}')
def get_entity(slug:str)->dict[str,Any]:
    e=public_store.entity_by_slug.get(slug)
    if e is None and not public_store.entity_by_slug:
        with sql_read.production_session() as session:payload=sql_read.entity(session,slug)
        if payload is None:raise HTTPException(404,'entity not found')
        return payload
    if e is None:raise HTTPException(404,'entity not found')
    ranks=[]
    for c in public_store.category_by_id.values():
        run=public_store.find_published_run(c.category_id)
        if not run:continue
        for r in public_store.ranking_store.results.get(run.id,()):
            if r.entity_id==e.id:
                p=public_store.previous_result(run,e.id);ranks.append({'ranking_result_id':str(r.id),'category_slug':c.slug,'category_name':c.name,'quarter':str(run.quarter),'rank':r.rank,'score':r.score,'previous_rank':p.rank if p else None,'movement':p.rank-r.rank if p else None,'confidence':r.confidence,'factor_coverage':r.factor_coverage,'factor_breakdown':r.factor_breakdown,'methodology_url':f'/v1/methodology/{c.methodology_slug}'})
    return {'id':str(e.id),'slug':e.slug,'name':e.name,'avatar_url':e.avatar_url,'summary':e.summary,'evidence_urls':e.evidence_urls,'current_rankings':ranks}
@router.get('/{slug}/history')
def get_entity_history(slug:str)->dict[str,Any]:
    e=public_store.entity_by_slug.get(slug)
    if e is None and not public_store.entity_by_slug:
        with sql_read.production_session() as session:payload=sql_read.history(session,slug)
        if payload is None:raise HTTPException(404,'entity not found')
        return payload
    if e is None:raise HTTPException(404,'entity not found')
    history=[]
    for run in public_store.ranking_store.runs.values():
        if run.status!=RankingRunStatus.PUBLISHED:continue
        c=public_store.category_by_id.get(run.category_id)
        if not c:continue
        for r in public_store.ranking_store.results.get(run.id,()):
            if r.entity_id==e.id:history.append({'quarter':str(run.quarter),'category_slug':c.slug,'rank':r.rank,'score':r.score,'factor_coverage':r.factor_coverage})
    history.sort(key=lambda x:x['quarter'],reverse=True);return {'entity_slug':slug,'history':history}
