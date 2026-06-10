from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.metrics import render_metrics
from app.core.middleware import RequestContextMiddleware
from app.db.bootstrap import bootstrap_database
from app.services.chat import ChatServiceError, ingest_if_requested
from app.ui.runner import start_streamlit_process, stop_streamlit_process

BASE_DIR = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    streamlit_process = None
    if app.state.run_startup_tasks:
        bootstrap_database()
        if settings.auto_ingest_on_startup:
            try:
                ingest_if_requested(force=False)
            except ChatServiceError:
                pass
    if app.state.run_streamlit:
        streamlit_process = start_streamlit_process(BASE_DIR, settings.streamlit_server_port)
    yield
    stop_streamlit_process(streamlit_process)


def create_app(run_startup_tasks: bool = True, run_streamlit: bool = True) -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.run_startup_tasks = run_startup_tasks
    app.state.run_streamlit = run_streamlit
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict:
        return {"status": "ok"}

    @app.get("/metrics", tags=["observability"])
    def metrics() -> Response:
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type)

    @app.get("/", tags=["root"])
    def root(request: Request):
        streamlit_url = (
            f"{request.url.scheme}://{request.url.hostname}:{settings.streamlit_server_port}"
        )
        return RedirectResponse(url=streamlit_url, status_code=307)

    return app


app = create_app()
