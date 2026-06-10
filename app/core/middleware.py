from __future__ import annotations

import time
from uuid import uuid4

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_TOTAL


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)

        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started

        path = request.url.path
        status_code = str(response.status_code)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status=status_code,
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=path,
        ).observe(elapsed)

        response.headers["X-Request-ID"] = request_id
        return response

