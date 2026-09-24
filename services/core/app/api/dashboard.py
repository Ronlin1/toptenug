from typing import Any
from fastapi import APIRouter
from app.domain.enums import RankingRunStatus
from .store import public_store
from . import sql_read
router=APIRouter(prefix='/v1',tags=['dashboard'])
@router.get('/dashboard')
def get_dashboard()->dict[str,Any]:
    if not public_store.category_by_slug:
        with sql_read.production_session() as session:return sql_read.dashboard(session)
    published=[r for r in public_store.ranking_store.runs.values() if r.status==RankingRunStatus.PUBLISHED];quarters=public_store.published_quarters();current=quarters[0] if quarters else None;runs=[r for r in published if str(r.quarter)==current];results=[x for r in runs for x in public_store.ranking_store.results.get(r.id,())]
    return {'current_quarter':current,'indexed_entities':len(public_store.entity_by_id),'active_rankings':len({r.category_id for r in runs}),'published_results':len(results),'source_links':sum(len(e.evidence_urls) for e in public_store.entity_by_id.values()),'biggest_movers':[],'categories':[{'slug':c.slug,'name':c.name,'ranking_type':c.ranking_type.value} for c in public_store.category_by_slug.values()]}
@router.get('/quarters')
def get_quarters()->dict[str,list[str]]:
    if not public_store.ranking_store.runs:
        with sql_read.production_session() as session:return {'quarters':sql_read.quarters(session)}
    return {'quarters':public_store.published_quarters()}
