from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.store import public_store

router = APIRouter(prefix="/v1", tags=["rankings"])


@router.get("/rankings/{slug}")
def get_ranking(slug: str, limit: int = Query(default=10), quarter: str | None = None) -> dict:
    if limit not in {10, 20, 30, 50}:
        raise HTTPException(status_code=422, detail="limit must be one of 10, 20, 30, or 50")
    run = public_store.get_published(slug, quarter)
    if run is None:
        raise HTTPException(status_code=404, detail="Published ranking not found")
    return {
        "slug": run.slug,
        "quarter": run.quarter,
        "ranking_type": run.ranking_type,
        "algorithm_name": run.algorithm_name,
        "algorithm_version": run.algorithm_version,
        "published_at": run.published_at,
        "methodology_url": run.methodology_url,
        "results": [
            {
                "result_id": result.id,
                "entity_id": result.entity_id,
                "slug": result.slug,
                "name": result.name,
                "rank": result.rank,
                "score": result.score,
                "previous_rank": result.previous_rank,
                "movement": None if result.previous_rank is None else result.previous_rank - result.rank,
                "confidence": result.confidence,
                "provenance_count": len(result.evidence_urls),
            }
            for result in run.results[:limit]
        ],
    }


@router.get("/rankings/results/{result_id}/share")
def get_share_metadata(result_id: UUID) -> dict:
    found = public_store.find_published_result(result_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Published ranking result not found")
    run, result = found
    return {
        "ranking_result_id": result.id,
        "entity_id": result.entity_id,
        "slug": result.slug,
        "name": result.name,
        "category": run.slug,
        "quarter": run.quarter,
        "ranking_type": run.ranking_type,
        "algorithm_name": run.algorithm_name,
        "algorithm_version": run.algorithm_version,
        "rank": result.rank,
        "score": result.score,
        "previous_rank": result.previous_rank,
        "movement": None if result.previous_rank is None else result.previous_rank - result.rank,
        "canonical_url": f"/people/{result.slug}",
    }


@router.get("/quarters")
def get_quarters() -> dict[str, list[str]]:
    return {"quarters": sorted({run.quarter for run in public_store.published_runs()}, reverse=True)}
