#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "services" / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from app.production_smoke import SmokeValidationError, validate_smoke_responses  # noqa: E402


def _get_json(client: httpx.Client, path: str, *, optional_404: bool = False) -> dict[str, Any] | None:
    response = client.get(path)
    if optional_404 and response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise SmokeValidationError(f"{path} did not return a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check a deployed TopTenUG API without exposing secrets.")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--quarter", default="2026-Q3")
    parser.add_argument("--category", default="github-developers")
    args = parser.parse_args()

    base = args.api_base_url.rstrip("/")
    try:
        with httpx.Client(base_url=base, timeout=20.0, follow_redirects=True) as client:
            health = _get_json(client, "/health")
            readiness = _get_json(client, "/ready")
            official = _get_json(
                client,
                f"/v1/rankings/{args.category}?limit=10&quarter={args.quarter}",
                optional_404=True,
            )
            preview = _get_json(
                client,
                f"/v1/preview/rankings/{args.category}?limit=10&quarter={args.quarter}",
                optional_404=True,
            )
        assert health is not None and readiness is not None
        validate_smoke_responses(
            health=health,
            readiness=readiness,
            official_ranking=official,
            preview_ranking=preview,
        )
    except (httpx.HTTPError, SmokeValidationError, ValueError) as exc:
        print(f"TopTenUG smoke check failed: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "api_base_url": base,
                "quarter": args.quarter,
                "category": args.category,
                "official_available": official is not None,
                "preview_available": preview is not None,
                "commit_sha": readiness.get("commit_sha"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
