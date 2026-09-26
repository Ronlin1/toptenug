from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings, get_settings


def _is_supabase_transaction_pooler(url: str) -> bool:
    return "pooler.supabase.com" in url and ":6543/" in url


def create_runtime_engine(settings: Settings) -> Engine:
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if _is_supabase_transaction_pooler(settings.database_url):
        kwargs["connect_args"] = {"prepare_threshold": None}
    return create_engine(settings.database_url, **kwargs)


def create_admin_engine(settings: Settings) -> Engine:
    if not settings.database_admin_url:
        raise ValueError("DATABASE_ADMIN_URL is required for administrative database operations")
    return create_engine(settings.database_admin_url, pool_pre_ping=True)


settings = get_settings()
engine = create_runtime_engine(settings)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
