import pytest

from app.production_smoke import SmokeValidationError, validate_smoke_responses


def test_smoke_accepts_healthy_official_surface() -> None:
    validate_smoke_responses(
        health={"status": "ok"},
        readiness={"status": "ready", "database_reachable": True, "commit_sha": "abc123"},
        official_ranking={"quarter": "2026-Q3", "results": [{"rank": 1}]},
        preview_ranking={"official": False, "results": [{"rank": 1}]},
    )


def test_smoke_rejects_degraded_database() -> None:
    with pytest.raises(SmokeValidationError, match="database"):
        validate_smoke_responses(
            health={"status": "ok"},
            readiness={"status": "degraded", "database_reachable": False, "commit_sha": "abc123"},
            official_ranking={"quarter": "2026-Q3", "results": []},
            preview_ranking=None,
        )


def test_smoke_rejects_preview_marked_official() -> None:
    with pytest.raises(SmokeValidationError, match="preview"):
        validate_smoke_responses(
            health={"status": "ok"},
            readiness={"status": "ready", "database_reachable": True, "commit_sha": "abc123"},
            official_ranking=None,
            preview_ranking={"official": True, "results": []},
        )
