from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import CHAT_TURNS_TOTAL
from app.db.bootstrap import bootstrap_database
from app.db.connection import get_db_connection
from app.db.repositories import (
    append_chat_message,
    count_chunks,
    create_session,
    latest_message_timestamp,
    list_recent_messages,
    search_similar_chunks,
)
from app.models.schemas import ChatRequest, ChatResponse, WeatherToolOutput
from app.services.conversation import (
    StoredMessage,
    extract_date_or_default,
    has_document_intent,
    trim_history,
    weather_intent,
)
from app.services.ingestion import ingest_pdf
from app.services.llm import get_chat_client, get_embeddings_client
from app.services.prompts import (
    build_chat_prompt,
    format_context,
    format_sources,
)
from app.services.weather import get_weather

logger = get_logger(__name__)


class ChatServiceError(RuntimeError):
    """Raised when the chat service cannot fulfill the request."""


def _resolve_session_id(raw_session_id: str | None) -> UUID:
    if raw_session_id:
        return UUID(raw_session_id)
    return uuid4()


def _history_mentions_weather(messages: list[StoredMessage]) -> bool:
    return any(weather_intent(message.content) for message in messages[-4:])


def _should_fetch_weather(user_message: str, history: list[StoredMessage]) -> bool:
    followup = any(token in user_message.lower() for token in ("hoy", "mañana", "manana"))
    return weather_intent(user_message) or (followup and _history_mentions_weather(history))


def _should_use_rag(user_message: str) -> bool:
    return has_document_intent(user_message) or not weather_intent(user_message)


def ingest_if_requested(force: bool = False) -> dict:
    settings = get_settings()
    if not settings.google_api_key:
        raise ChatServiceError("Falta GOOGLE_API_KEY para indexar el corpus documental.")
    return ingest_pdf(force_reindex=force)


def _ensure_indexed() -> None:
    with get_db_connection() as connection:
        current_chunks = count_chunks(connection)

    if current_chunks > 0:
        return

    settings = get_settings()
    if not settings.auto_ingest_on_startup:
        raise ChatServiceError(
            "La base vectorial esta vacia. Ejecuta la ingesta antes de usar el chat."
        )

    ingest_if_requested(force=True)


def _retrieve_documents(question: str) -> list[dict]:
    settings = get_settings()
    query_embedding = get_embeddings_client().embed_query(question)
    with get_db_connection() as connection:
        return search_similar_chunks(connection, query_embedding, settings.rag_top_k)


def chat_with_tenerife(payload: ChatRequest) -> ChatResponse:
    settings = get_settings()
    if not settings.google_api_key:
        raise ChatServiceError("Falta GOOGLE_API_KEY para usar el chat conversacional.")

    bootstrap_database()
    _ensure_indexed()

    session_id = _resolve_session_id(payload.session_id)

    with get_db_connection() as connection:
        create_session(connection, session_id)
        stored_history = trim_history(list_recent_messages(connection, session_id=session_id))

    weather_result: WeatherToolOutput | None = None
    if _should_fetch_weather(payload.message, stored_history):
        weather_result = get_weather(extract_date_or_default(payload.message))

    rag_used = _should_use_rag(payload.message)
    documents = _retrieve_documents(payload.message) if rag_used else []
    prompt = build_chat_prompt(
        user_message=payload.message,
        history=stored_history,
        context=format_context(documents),
        weather=weather_result,
    )

    response = get_chat_client().invoke(
        [
            SystemMessage(
                content=(
                    "Actua como guia turistico fiable de Tenerife. "
                    "No inventes datos y resume con claridad."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )
    answer = str(response.content).strip()
    sources = format_sources(documents) if rag_used else []

    metadata = {
        "rag_used": rag_used,
        "weather_used": bool(weather_result),
        "source_count": len(sources),
    }

    with get_db_connection() as connection:
        append_chat_message(connection, session_id=session_id, role="user", content=payload.message)
        append_chat_message(
            connection,
            session_id=session_id,
            role="assistant",
            content=answer,
            metadata=metadata,
        )
        created_at = latest_message_timestamp(connection, session_id) or datetime.utcnow()

    logger.info(
        "chat_turn_completed",
        session_id=str(session_id),
        rag_used=rag_used,
        weather_used=bool(weather_result),
        source_count=len(sources),
    )
    CHAT_TURNS_TOTAL.labels(
        rag_used=str(rag_used).lower(),
        weather_used=str(bool(weather_result)).lower(),
    ).inc()

    return ChatResponse(
        session_id=str(session_id),
        answer=answer,
        sources=sources,
        weather=weather_result,
        rag_used=rag_used,
        created_at=created_at,
        metadata=metadata,
    )
