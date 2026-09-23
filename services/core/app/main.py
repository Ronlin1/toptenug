from fastapi import FastAPI

from app.api.dashboard import router as dashboard_router
from app.api.entities import router as entities_router
from app.api.methodology import router as methodology_router
from app.api.rankings import router as rankings_router

app = FastAPI(title="TopTenUG Core", version="0.1.0")
app.include_router(rankings_router)
app.include_router(entities_router)
app.include_router(dashboard_router)
app.include_router(methodology_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
