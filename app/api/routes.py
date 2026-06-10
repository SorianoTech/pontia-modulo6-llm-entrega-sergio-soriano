from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse, InfoCard
from app.services.chat import (
    ChatServiceError,
    chat_with_tenerife,
    ingest_if_requested,
)
from app.services.content import get_info_cards

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/info", response_model=list[InfoCard], tags=["info"])
def get_info() -> list[InfoCard]:
    return get_info_cards()


@api_router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    try:
        return chat_with_tenerife(payload)
    except ChatServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@api_router.post("/ingest", tags=["admin"])
def ingest_endpoint() -> dict:
    try:
        return ingest_if_requested(force=True)
    except ChatServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
