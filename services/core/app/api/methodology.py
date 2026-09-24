from typing import Any
from fastapi import APIRouter,HTTPException
from .store import public_store
from . import sql_read
router=APIRouter(prefix='/v1/methodology',tags=['methodology'])
@router.get('/{slug}')
def get_methodology(slug:str)->dict[str,Any]:
    c=next((x for x in public_store.category_by_slug.values() if x.methodology_slug==slug),None)
    if c is None:
        with sql_read.production_session() as session:payload=sql_read.methodology(session,slug)
        if payload is None:raise HTTPException(404,'methodology not found')
        return payload
    snap=public_store.ranking_store.category_inputs.get(c.category_id)
    if snap is None:raise HTTPException(404,'methodology not configured')
    s=snap.spec;return {'slug':slug,'name':s.name,'version':s.version,'ranking_type':s.ranking_type.value,'eligibility_policy':s.eligibility_policy,'missing_data_policy':s.missing_data_policy,'minimum_factor_coverage':s.minimum_factor_coverage,'tie_breaker':s.tie_breaker,'factors':{n:f.model_dump() for n,f in s.factors.items()},'limitations':['GitHub activity is not a universal measure of developer quality.','Private and non-GitHub work may be underrepresented.','Google/Gemini discovery and search order are not ranking factors.']}
