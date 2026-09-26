from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from os import getenv
from typing import Literal, cast

Environment = Literal["local", "staging", "production"]


def _environment_env() -> Environment:
    value = getenv("TOPTENUG_ENVIRONMENT", "local")
    if value not in {"local", "staging", "production"}:
        raise ValueError("TOPTENUG_ENVIRONMENT must be local, staging, or production")
    return cast(Environment, value)


def _csv_env(name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in getenv(name, default).split(",") if value.strip())


def _bool_env(name: str, default: bool = False) -> bool:
    raw = getenv(name)
    if raw is None:
        return default
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    environment: Environment = field(default_factory=_environment_env)
    database_url: str = field(
        default_factory=lambda: getenv(
            "DATABASE_URL",
            "postgresql+psycopg://toptenug@localhost:5432/toptenug",
        )
    )
    database_admin_url: str | None = field(default_factory=lambda: getenv("DATABASE_ADMIN_URL"))
    allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: _csv_env("TOPTENUG_ALLOWED_ORIGINS", "http://localhost:3000")
    )
    commit_sha: str = field(default_factory=lambda: getenv("TOPTENUG_COMMIT_SHA", "dev"))
    provisional_public_enabled: bool = field(
        default_factory=lambda: _bool_env("TOPTENUG_PROVISIONAL_PUBLIC_ENABLED", False)
    )
    github_token: str | None = field(default_factory=lambda: getenv("GITHUB_TOKEN"))
    github_api_base_url: str = field(
        default_factory=lambda: getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    )
    gemini_api_key: str | None = field(default_factory=lambda: getenv("GEMINI_API_KEY"))
    gemini_model: str = field(default_factory=lambda: getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    public_web_base_url: str = field(
        default_factory=lambda: getenv("TOPTENUG_PUBLIC_BASE_URL", "http://localhost:3000")
    )

    def __post_init__(self) -> None:
        if self.environment == "local" and not self.database_admin_url:
            self.database_admin_url = self.database_url

        if self.environment in {"staging", "production"}:
            if not self.database_url:
                raise ValueError("DATABASE_URL is required outside local development")
            if not self.database_admin_url:
                raise ValueError("DATABASE_ADMIN_URL is required outside local development")
            if not self.allowed_origins:
                raise ValueError("TOPTENUG_ALLOWED_ORIGINS is required outside local development")


@lru_cache
def get_settings() -> Settings:
    return Settings()
