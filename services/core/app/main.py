from __future__ import annotations

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dashboard import router as dashboard_router
from app.api.entities import router as entities_router
from app.api.methodology import router as methodology_router
from app.api.preview import router as preview_router
from app.api.rankings import router as rankings_router
from app.config import get_settings
from app.db import engine

APP_VERSION = "0.1.0"
settings = get_settings()

app = FastAPI(title="TopTenUG Core", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_origin_regex=r"https://.*\.vercel\.app" if settings.environment == "staging" else None,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(dashboard_router)
app.include_router(rankings_router)
app.include_router(preview_router)
app.include_router(entities_router)
app.include_router(methodology_router)


def database_reachable() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response) -> dict[str, str | bool]:
    reachable = database_reachable()
    if not reachable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if reachable else "degraded",
        "environment": settings.environment,
        "commit_sha": settings.commit_sha,
        "database_reachable": reachable,
        "version": APP_VERSION,
    }
