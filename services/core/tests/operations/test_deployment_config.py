import json

import pytest

from app.deployment_config import DeploymentConfigError, validate_deployment_config


def _env(**overrides: str) -> dict[str, str]:
    values = {
        "TOPTENUG_ENVIRONMENT": "staging",
        "TOPTENUG_GCP_PROJECT_ID": "toptenug-staging-project",
        "TOPTENUG_GCP_REGION": "europe-west3",
        "TOPTENUG_ARTIFACT_REPOSITORY": "toptenug",
        "TOPTENUG_SUPABASE_REGION": "eu-central-1",
        "DATABASE_URL": "postgresql+psycopg://postgres.project@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
        "DATABASE_ADMIN_URL": "postgresql+psycopg://postgres@db.project.supabase.co:5432/postgres",
        "GITHUB_TOKEN": "github-configured-placeholder",
        "GEMINI_API_KEY": "gemini-configured-placeholder",
        "TOPTENUG_PUBLIC_BASE_URL": "https://preview.toptenug.example",
        "TOPTENUG_ALLOWED_ORIGINS": "https://preview.toptenug.example",
        "TOPTENUG_COMMIT_SHA": "abc1234",
        "TOPTENUG_PREVIEW_API_BASE_URL": "https://api-staging.toptenug.example",
        "TOPTENUG_PRODUCTION_API_BASE_URL": "https://api.toptenug.example",
        "NEXT_PUBLIC_API_BASE_URL": "https://api-staging.toptenug.example",
    }
    values.update(overrides)
    return values


def test_defaults_pin_frankfurt_region_pair() -> None:
    config = validate_deployment_config(_env())

    assert config.supabase_region == "eu-central-1"
    assert config.gcp_region == "europe-west3"


def test_rejects_same_preview_and_production_api_url() -> None:
    with pytest.raises(DeploymentConfigError, match="Preview and production API URLs must differ"):
        validate_deployment_config(
            _env(
                TOPTENUG_PREVIEW_API_BASE_URL="https://api.toptenug.example",
                TOPTENUG_PRODUCTION_API_BASE_URL="https://api.toptenug.example",
            )
        )


def test_rejects_missing_admin_url_outside_local() -> None:
    with pytest.raises(DeploymentConfigError, match="DATABASE_ADMIN_URL"):
        validate_deployment_config(_env(DATABASE_ADMIN_URL=""))


def test_rejects_transaction_pooler_as_admin_connection() -> None:
    with pytest.raises(DeploymentConfigError, match="direct Supabase connection"):
        validate_deployment_config(
            _env(
                DATABASE_ADMIN_URL="postgresql+psycopg://postgres.project@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
            )
        )


def test_runtime_uses_transaction_pooler_and_admin_uses_direct_connection() -> None:
    config = validate_deployment_config(_env())

    assert config.runtime_uses_transaction_pooler
    assert not config.admin_uses_transaction_pooler
    assert config.disable_prepared_statements


def test_rejects_region_pair_drift() -> None:
    with pytest.raises(DeploymentConfigError, match="region pair"):
        validate_deployment_config(_env(TOPTENUG_GCP_REGION="us-central1"))


def test_loggable_summary_redacts_all_secret_values() -> None:
    env = _env()
    config = validate_deployment_config(env)
    rendered = json.dumps(config.loggable_summary(), sort_keys=True)

    assert env["GITHUB_TOKEN"] not in rendered
    assert env["GEMINI_API_KEY"] not in rendered
    assert config.loggable_summary()["github_token_configured"] is True
    assert config.loggable_summary()["gemini_api_key_configured"] is True


def test_next_public_api_must_match_target_environment() -> None:
    with pytest.raises(DeploymentConfigError, match="NEXT_PUBLIC_API_BASE_URL"):
        validate_deployment_config(
            _env(NEXT_PUBLIC_API_BASE_URL="https://api.toptenug.example")
        )
