from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import RankingRunStatus
from app.domain.models import AlgorithmDefinition, Entity, RankingCategory, RankingResult, RankingRun

from . import sql_read
from .rankings import PublicLimit

router = APIRouter(prefix="/v1/preview", tags=["preview"])


def preview_ranking(
    session: Session,
    slug: str,
    limit: int,
    quarter: str,
) -> dict[str, Any] | None:
    category = session.scalar(select(RankingCategory).where(RankingCategory.slug == slug))
    if category is None:
        return None
    run = session.scalar(
        select(RankingRun)
        .where(
            RankingRun.category_id == category.id,
            RankingRun.status == RankingRunStatus.PROVISIONAL,
            RankingRun.quarter == quarter,
        )
        .order_by(RankingRun.started_at.desc(), RankingRun.id.desc())
    )
    if run is None:
        return None
    algorithm = session.get(AlgorithmDefinition, run.algorithm_id)
    rows = session.scalars(
        select(RankingResult)
        .where(RankingResult.ranking_run_id == run.id)
        .order_by(RankingResult.rank)
        .limit(limit)
    ).all()
    results: list[dict[str, Any]] = []
    for row in rows:
        entity = session.get(Entity, row.entity_id)
        results.append(
            {
                "ranking_result_id": str(row.id),
                "entity_id": str(row.entity_id),
                "entity_slug": entity.slug if entity else str(row.entity_id),
                "name": entity.name if entity else str(row.entity_id),
                "rank": row.rank,
                "score": row.score,
                "confidence": row.confidence,
                "factor_coverage": float(row.provenance_summary.get("factor_coverage", 1.0)),
                "factor_breakdown": row.factor_breakdown,
                "profile_url": f"/v1/entities/{entity.slug}" if entity else None,
            }
        )
    return {
        "slug": category.slug,
        "name": category.name,
        "quarter": run.quarter,
        "ranking_type": category.ranking_type.value,
        "algorithm_name": algorithm.name if algorithm else "Unknown",
        "algorithm_version": algorithm.version if algorithm else "unknown",
        "official": False,
        "reviewed_pool_count": run.candidate_count,
        "cutoff_at": run.cutoff_at.isoformat() if run.cutoff_at else None,
        "limit": limit,
        "results": results,
    }


@router.get("/rankings/{slug}")
def get_preview_ranking(
    slug: str,
    limit: PublicLimit = Query(default=PublicLimit.TEN),
    quarter: str = Query(pattern=r"^\d{4}-Q[1-4]$"),
) -> dict[str, Any]:
    with sql_read.production_session() as session:
        payload = preview_ranking(session, slug, int(limit), quarter)
    if payload is None:
        raise HTTPException(404, "provisional ranking not found")
    return payload
