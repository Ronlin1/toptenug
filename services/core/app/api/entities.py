from fastapi import APIRouter, HTTPException

from app.api.store import public_store

router = APIRouter(prefix="/v1/entities", tags=["entities"])


def _appearances(slug: str):
    return [
        (run, result)
        for run in public_store.published_runs()
        for result in run.results
        if result.slug == slug
    ]


@router.get("/{slug}")
def entity(slug: str) -> dict:
    rows = _appearances(slug)
    if not rows:
        raise HTTPException(status_code=404, detail="Entity not found")
    latest_run, latest = sorted(rows, key=lambda row: row[0].quarter, reverse=True)[0]
    return {
        "entity_id": latest.entity_id,
        "slug": latest.slug,
        "name": latest.name,
        "current_rankings": [
            {
                "ranking": run.slug,
                "quarter": run.quarter,
                "rank": result.rank,
                "score": result.score,
                "confidence": result.confidence,
                "factor_breakdown": result.factor_breakdown or {},
                "evidence_urls": result.evidence_urls,
            }
            for run, result in rows
            if run.quarter == latest_run.quarter
        ],
    }


@router.get("/{slug}/history")
def entity_history(slug: str) -> dict:
    rows = _appearances(slug)
    if not rows:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {
        "slug": slug,
        "history": [
            {"ranking": run.slug, "quarter": run.quarter, "rank": result.rank, "score": result.score}
            for run, result in sorted(rows, key=lambda row: row[0].quarter)
        ],
    }
