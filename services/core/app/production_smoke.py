from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class SmokeValidationError(ValueError):
    """Raised when a deployed TopTenUG surface violates the smoke contract."""


def validate_smoke_responses(
    *,
    health: Mapping[str, Any],
    readiness: Mapping[str, Any],
    official_ranking: Mapping[str, Any] | None,
    preview_ranking: Mapping[str, Any] | None,
) -> None:
    if health.get("status") != "ok":
        raise SmokeValidationError("health endpoint is not ok")
    if readiness.get("status") != "ready" or readiness.get("database_reachable") is not True:
        raise SmokeValidationError("database readiness check is degraded")
    if not str(readiness.get("commit_sha") or "").strip():
        raise SmokeValidationError("readiness response is missing commit_sha")

    if preview_ranking is not None and preview_ranking.get("official") is not False:
        raise SmokeValidationError("preview ranking must be explicitly non-official")

    if official_ranking is not None:
        if official_ranking.get("official") is False:
            raise SmokeValidationError("official ranking surface returned provisional metadata")
        results = official_ranking.get("results")
        if not isinstance(results, list):
            raise SmokeValidationError("official ranking results must be a list")

    if preview_ranking is not None:
        results = preview_ranking.get("results")
        if not isinstance(results, list):
            raise SmokeValidationError("preview ranking results must be a list")
