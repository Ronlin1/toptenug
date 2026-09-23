from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.ranking.loader import load_algorithm_spec

router = APIRouter(prefix="/v1/methodology", tags=["methodology"])


@router.get("/{slug}")
def methodology(slug: str) -> dict:
    if slug != "devrankug-v1":
        raise HTTPException(status_code=404, detail="Methodology not found")
    spec = load_algorithm_spec(Path("algorithms/devrankug/v1.0.0.yaml"))
    return {
        "name": spec.name,
        "version": spec.version,
        "ranking_type": spec.ranking_type,
        "eligibility_policy": spec.eligibility_policy,
        "missing_data_policy": spec.missing_data_policy,
        "minimum_factor_coverage": spec.minimum_factor_coverage,
        "tie_breaker": spec.tie_breaker,
        "factors": [factor.__dict__ for factor in spec.factors],
        "limitations": [
            "GitHub hard metrics do not measure every form of engineering impact.",
            "Google/Gemini discovery relevance is not a ranking signal.",
        ],
    }
