from fastapi import APIRouter

from app.api.store import public_store

router = APIRouter(prefix="/v1", tags=["dashboard"])


@router.get("/dashboard")
def dashboard() -> dict:
    runs = public_store.published_runs()
    entity_ids = {result.entity_id for run in runs for result in run.results}
    quarters = sorted({run.quarter for run in runs}, reverse=True)
    return {
        "current_quarter": quarters[0] if quarters else None,
        "indexed_entities": len(entity_ids),
        "active_rankings": len({run.slug for run in runs}),
        "published_snapshots": len(runs),
    }
