from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlsplit


class DeploymentConfigError(ValueError):
    pass


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "").strip()
    if not value:
        raise DeploymentConfigError(f"{name} is required")
    return value


def _endpoint(url: str) -> tuple[str, int | None]:
    parsed = urlsplit(url)
    return (parsed.hostname or "", parsed.port)


def _uses_transaction_pooler(url: str) -> bool:
    host, port = _endpoint(url)
    return port == 6543 or "pooler.supabase.com" in host


@dataclass(frozen=True)
class DeploymentConfig:
    environment: str
    gcp_project_id: str
    gcp_region: str
    artifact_repository: str
    supabase_region: str
    database_url: str
    database_admin_url: str
    public_base_url: str
    allowed_origins: tuple[str, ...]
    commit_sha: str
    preview_api_base_url: str
    production_api_base_url: str
    next_public_api_base_url: str
    github_token_configured: bool
    gemini_api_key_configured: bool
    runtime_uses_transaction_pooler: bool
    admin_uses_transaction_pooler: bool
    disable_prepared_statements: bool

    def loggable_summary(self) -> dict[str, object]:
        runtime_host, runtime_port = _endpoint(self.database_url)
        admin_host, admin_port = _endpoint(self.database_admin_url)
        return {
            "environment": self.environment,
            "gcp_project_id": self.gcp_project_id,
            "gcp_region": self.gcp_region,
            "artifact_repository": self.artifact_repository,
            "supabase_region": self.supabase_region,
            "runtime_database_endpoint": f"{runtime_host}:{runtime_port or ''}",
            "admin_database_endpoint": f"{admin_host}:{admin_port or ''}",
            "public_base_url": self.public_base_url,
            "allowed_origins": self.allowed_origins,
            "commit_sha": self.commit_sha,
            "preview_api_base_url": self.preview_api_base_url,
            "production_api_base_url": self.production_api_base_url,
            "next_public_api_base_url": self.next_public_api_base_url,
            "github_token_configured": self.github_token_configured,
            "gemini_api_key_configured": self.gemini_api_key_configured,
            "runtime_uses_transaction_pooler": self.runtime_uses_transaction_pooler,
            "admin_uses_transaction_pooler": self.admin_uses_transaction_pooler,
            "disable_prepared_statements": self.disable_prepared_statements,
        }


def validate_deployment_config(env: Mapping[str, str]) -> DeploymentConfig:
    environment = _required(env, "TOPTENUG_ENVIRONMENT")
    if environment not in {"staging", "production"}:
        raise DeploymentConfigError("deployment validation supports staging or production")

    gcp_project_id = _required(env, "TOPTENUG_GCP_PROJECT_ID")
    gcp_region = env.get("TOPTENUG_GCP_REGION", "europe-west3").strip() or "europe-west3"
    artifact_repository = _required(env, "TOPTENUG_ARTIFACT_REPOSITORY")
    supabase_region = env.get("TOPTENUG_SUPABASE_REGION", "eu-central-1").strip() or "eu-central-1"
    database_url = _required(env, "DATABASE_URL")
    database_admin_url = _required(env, "DATABASE_ADMIN_URL")
    public_base_url = _required(env, "TOPTENUG_PUBLIC_BASE_URL")
    allowed_origins = tuple(
        value.strip() for value in _required(env, "TOPTENUG_ALLOWED_ORIGINS").split(",") if value.strip()
    )
    commit_sha = _required(env, "TOPTENUG_COMMIT_SHA")
    preview_api_base_url = _required(env, "TOPTENUG_PREVIEW_API_BASE_URL").rstrip("/")
    production_api_base_url = _required(env, "TOPTENUG_PRODUCTION_API_BASE_URL").rstrip("/")
    next_public_api_base_url = _required(env, "NEXT_PUBLIC_API_BASE_URL").rstrip("/")

    if (supabase_region, gcp_region) != ("eu-central-1", "europe-west3"):
        raise DeploymentConfigError(
            "TopTenUG Phase 2 region pair must remain Supabase eu-central-1 + Cloud Run europe-west3"
        )
    if preview_api_base_url == production_api_base_url:
        raise DeploymentConfigError("Preview and production API URLs must differ")

    runtime_pooler = _uses_transaction_pooler(database_url)
    admin_pooler = _uses_transaction_pooler(database_admin_url)
    if not runtime_pooler:
        raise DeploymentConfigError("DATABASE_URL must use the Supabase transaction pooler")
    if admin_pooler:
        raise DeploymentConfigError("DATABASE_ADMIN_URL must use the direct Supabase connection, not the transaction pooler")
    if _endpoint(database_url) == _endpoint(database_admin_url):
        raise DeploymentConfigError("runtime and admin database endpoints must be distinct")

    expected_public_api = preview_api_base_url if environment == "staging" else production_api_base_url
    if next_public_api_base_url != expected_public_api:
        raise DeploymentConfigError(
            f"NEXT_PUBLIC_API_BASE_URL must match the {environment} API URL"
        )

    return DeploymentConfig(
        environment=environment,
        gcp_project_id=gcp_project_id,
        gcp_region=gcp_region,
        artifact_repository=artifact_repository,
        supabase_region=supabase_region,
        database_url=database_url,
        database_admin_url=database_admin_url,
        public_base_url=public_base_url,
        allowed_origins=allowed_origins,
        commit_sha=commit_sha,
        preview_api_base_url=preview_api_base_url,
        production_api_base_url=production_api_base_url,
        next_public_api_base_url=next_public_api_base_url,
        github_token_configured=bool(env.get("GITHUB_TOKEN", "").strip()),
        gemini_api_key_configured=bool(env.get("GEMINI_API_KEY", "").strip()),
        runtime_uses_transaction_pooler=runtime_pooler,
        admin_uses_transaction_pooler=admin_pooler,
        disable_prepared_statements=True,
    )
