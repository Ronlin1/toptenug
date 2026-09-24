from dataclasses import dataclass
from functools import lru_cache
from os import getenv


@dataclass(frozen=True)
class Settings:
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql+psycopg://toptenug:toptenug@localhost:5432/toptenug",
    )
    github_token: str | None = getenv("GITHUB_TOKEN")
    github_api_base_url: str = getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    gemini_api_key: str | None = getenv("GEMINI_API_KEY")
    gemini_model: str = getenv("GEMINI_MODEL", "gemini-2.5-flash")
    public_web_base_url: str = getenv("TOPTENUG_PUBLIC_BASE_URL", "http://localhost:3000")


@lru_cache
def get_settings() -> Settings:
    return Settings()
