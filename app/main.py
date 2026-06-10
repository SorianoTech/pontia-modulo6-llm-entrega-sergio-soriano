from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.bootstrap import bootstrap_database
from app.models.schemas import InfoCard
from app.services.chat import ChatServiceError, ingest_if_requested
from app.services.content import get_info_cards


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if app.state.run_startup_tasks:
        bootstrap_database()
        if settings.auto_ingest_on_startup:
            try:
                ingest_if_requested(force=False)
            except ChatServiceError:
                pass
    yield


def create_app(run_startup_tasks: bool = True) -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.run_startup_tasks = run_startup_tasks
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict:
        return {"status": "ok"}

    @app.get("/", response_model=list[InfoCard], tags=["root"])
    def root() -> list[InfoCard]:
        return get_info_cards()

    return app


app = create_app()

