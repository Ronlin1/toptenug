from __future__ import annotations

import pytest

from app.config import Settings
from app import db


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "production",
        "database_url": "postgresql+psycopg://runtime@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
        "database_admin_url": "postgresql+psycopg://admin@db.example.supabase.co:5432/postgres",
        "allowed_origins": ("https://toptenug.example",),
        "commit_sha": "abc1234",
        "provisional_public_enabled": False,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_production_requires_database_and_public_origin() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        production_settings(database_url="")

    with pytest.raises(ValueError, match="TOPTENUG_ALLOWED_ORIGINS"):
        production_settings(allowed_origins=())


def test_runtime_engine_disables_psycopg_prepare_for_transaction_pooler(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_create_engine(url: str, **kwargs: object) -> object:
        captured["url"] = url
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    settings = production_settings()

    engine = db.create_runtime_engine(settings)

    assert engine is sentinel
    assert captured["url"] == settings.database_url
    assert captured["pool_pre_ping"] is True
    assert captured["connect_args"] == {"prepare_threshold": None}


def test_admin_url_is_separate_from_runtime_pooler_url(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_create_engine(url: str, **kwargs: object) -> object:
        calls.append((url, kwargs))
        return object()

    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    settings = production_settings()

    db.create_runtime_engine(settings)
    db.create_admin_engine(settings)

    assert calls[0][0] == settings.database_url
    assert calls[1][0] == settings.database_admin_url
    assert calls[0][0] != calls[1][0]
    assert calls[1][1].get("connect_args") != {"prepare_threshold": None}
