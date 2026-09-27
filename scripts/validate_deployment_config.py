#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "services" / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from app.deployment_config import DeploymentConfigError, validate_deployment_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TopTenUG hybrid deployment configuration without printing secrets.")
    parser.add_argument("--environment", choices=("staging", "production"), required=True)
    args = parser.parse_args()

    env = dict(os.environ)
    env["TOPTENUG_ENVIRONMENT"] = args.environment
    try:
        config = validate_deployment_config(env)
    except DeploymentConfigError as exc:
        print(f"deployment config invalid: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(config.loggable_summary(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
