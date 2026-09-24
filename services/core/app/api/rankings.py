from enum import IntEnum
from typing import Any
from uuid import UUID
from fastapi import APIRouter,HTTPException,Query
from app.config import get_settings
from app.domain.enums import RankingRunStatus
from app.quarterly.publish import PublishedResult,PublishedRun
from .store import CategoryPublicRecord,public_store
from . import sql_read
router=APIRouter(prefix='/v1',tags=['rankings'])
class PublicLimit(IntEnum):TEN=10;TWENTY=20;THIRTY=30;FIFTY=50
def _result_payload(run:PublishedRun,result:PublishedResult,category:CategoryPublicRecord)->dict[str,Any]:
    e=public_store.entity_by_id.get(result.entity_id);prev=public_store.previous_result(run,result.entity_id);pr=prev.rank if prev else None
    return {'ranking_result_id':str(result.id),'entity_id':str(result.entity_id),'entity_slug':e.slug if e else str(result.entity_id),'name':e.name if e else str(result.entity_id),'avatar_url':e.avatar_url if e else None,'rank':result.rank,'score':result.score,'previous_rank':pr,'movement':pr-result.rank if pr is not None else None,'confidence':result.confidence,'factor_coverage':result.factor_coverage,'factor_breakdown':result.factor_breakdown,'provenance':{'source_count':len(e.evidence_urls) if e else 0,'source_urls':e.evidence_urls if e else []},'profile_url':f'/v1/entities/{e.slug}' if e else None}
@router.get('/rankings/{slug}')
def get_ranking(slug:str,limit:PublicLimit=Query(default=PublicLimit.TEN),quarter:str|None=Query(default=None,pattern=r'^\d{4}-Q[1-4]$'))->dict[str,Any]:
    c=public_store.category_by_slug.get(slug)
    if c is None:
        with sql_read.production_session() as session:payload=sql_read.ranking(session,slug,int(limit),quarter)
        if payload is None:raise HTTPException(404,'ranking category not found')
        return payload
    run=public_store.find_published_run(c.category_id,quarter)
    if run is None:raise HTTPException(404,'published ranking not found')
    results=sorted(public_store.ranking_store.results.get(run.id,()),key=lambda x:x.rank)
    return {'slug':c.slug,'name':c.name,'quarter':str(run.quarter),'ranking_type':c.ranking_type.value,'algorithm_name':run.algorithm_name,'algorithm_version':run.algorithm_version,'published_at':run.published_at,'methodology_url':f'/v1/methodology/{c.methodology_slug}','limit':int(limit),'results':[_result_payload(run,r,c) for r in results[:int(limit)]]}
def get_published_result_by_id(rid:UUID)->tuple[PublishedRun,PublishedResult,CategoryPublicRecord]|None:
    for run_id,results in public_store.ranking_store.results.items():
        run=public_store.ranking_store.runs.get(run_id)
        if run is None or run.status!=RankingRunStatus.PUBLISHED:continue
        for result in results:
            if result.id==rid:return run,result,public_store.category_by_id[run.category_id]
    return None
@router.get('/rankings/results/{result_id}/share')
def get_share_metadata(result_id:UUID)->dict[str,Any]:
    found=get_published_result_by_id(result_id)
    if found is None and not public_store.category_by_slug:
        with sql_read.production_session() as session:payload=sql_read.share(session,result_id)
        if payload is None:raise HTTPException(404,'published ranking result not found')
        return payload
    if found is None:raise HTTPException(404,'published ranking result not found')
    run,result,c=found;e=public_store.entity_by_id.get(result.entity_id)
    if e is None:raise HTTPException(404,'ranked entity not found')
    prev=public_store.previous_result(run,result.entity_id);pr=prev.rank if prev else None;base=get_settings().public_web_base_url.rstrip('/')
    return {'ranking_result_id':str(result.id),'rank':result.rank,'score':result.score,'movement':pr-result.rank if pr is not None else None,'entity_name':e.name,'entity_slug':e.slug,'category_name':c.name,'category_slug':c.slug,'ranking_type':c.ranking_type.value,'quarter':str(run.quarter),'algorithm_name':run.algorithm_name,'algorithm_version':run.algorithm_version,'canonical_url':f'{base}/people/{e.slug}','image_path':f'/api/share/{result.id}'}
