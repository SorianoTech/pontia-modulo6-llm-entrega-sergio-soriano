from __future__ import annotations

from datetime import datetime
from time import perf_counter
from uuid import UUID, uuid4

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import (
    CHAT_SOURCE_COUNT,
    CHAT_TURNS_TOTAL,
    LLM_INPUT_TOKENS_TOTAL,
    LLM_OUTPUT_TOKENS_TOTAL,
    LLM_REQUEST_DURATION_SECONDS,
    LLM_REQUESTS_TOTAL,
    LLM_TOTAL_TOKENS_TOTAL,
    WEATHER_TOOL_CALLS_TOTAL,
)
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
from app.services.llm import (
    get_chat_client,
    get_embeddings_client,
    get_generation_model_name,
    require_embedding_configuration,
    require_generation_configuration,
)
from app.services.llm_usage import extract_token_usage
from app.services.prompts import (
    build_chat_prompt,
    format_context,
    format_sources,
)
from app.services.weather import get_weather

logger = get_logger(__name__)


class ChatServiceError(RuntimeError):
    """Raised when the chat service cannot fulfill the request."""


def _serialize_chunk_for_audit(document: dict) -> dict:
    """Extract a compact chunk summary suitable for audit logs."""
    metadata = document.get("metadata") or {}
    similarity = document.get("similarity")
    return {
        "chunk_key": document.get("chunk_key"),
        "source_name": document.get("source_name"),
        "chunk_id": document.get("chunk_id"),
        "page": document.get("page"),
        "page_label": metadata.get("page_label"),
        "similarity": None if similarity is None else round(float(similarity), 4),
        "content": document.get("content"),
    }


def _resolve_session_id(raw_session_id: str | None) -> UUID:
    """Return the provided session identifier or create a new one for first-time users."""
    if raw_session_id:
        return UUID(raw_session_id)
    return uuid4()


def _history_mentions_weather(messages: list[StoredMessage]) -> bool:
    """Check whether the recent conversation context already discussed weather."""
    return any(weather_intent(message.content) for message in messages[-4:])


def _should_fetch_weather(user_message: str, history: list[StoredMessage]) -> bool:
    """Decide whether a turn should call the weather tool."""
    followup = any(token in user_message.lower() for token in ("hoy", "mañana", "manana"))
    return weather_intent(user_message) or (followup and _history_mentions_weather(history))


def _should_use_rag(user_message: str) -> bool:
    """Decide whether the response should retrieve supporting document chunks."""
    return has_document_intent(user_message) or not weather_intent(user_message)


def ingest_if_requested(force: bool = False) -> dict:
    """Run ingestion when configured dependencies for document indexing are available."""
    try:
        require_embedding_configuration()
    except RuntimeError as exc:
        raise ChatServiceError(str(exc)) from exc
    return ingest_pdf(force_reindex=force)


def _ensure_indexed() -> None:
    """Guarantee that the vector index contains at least one chunk before chatting."""
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
    """Embed the user question and retrieve the most similar indexed chunks."""
    settings = get_settings()
    query_embedding = get_embeddings_client().embed_query(question)
    with get_db_connection() as connection:
        return search_similar_chunks(connection, query_embedding, settings.rag_top_k)


def chat_with_tenerife(payload: ChatRequest) -> ChatResponse:
    """Process a conversational turn with RAG, optional weather lookup, and persistence."""
    try:
        require_generation_configuration()
        require_embedding_configuration()
    except RuntimeError as exc:
        raise ChatServiceError(str(exc)) from exc

    generation_model_name = get_generation_model_name()

    bootstrap_database()
    _ensure_indexed()

    session_id = _resolve_session_id(payload.session_id)

    with get_db_connection() as connection:
        create_session(connection, session_id)
        stored_history = trim_history(list_recent_messages(connection, session_id=session_id))

    user_has_weather_intent = weather_intent(payload.message)
    user_has_document_intent = has_document_intent(payload.message)
    history_mentions_weather = _history_mentions_weather(stored_history)
    weather_requested = _should_fetch_weather(payload.message, stored_history)
    rag_used = _should_use_rag(payload.message)

    logger.info(
        "chat_strategy_selected",
        session_id=str(session_id),
        user_message=payload.message,
        rag_used=rag_used,
        weather_requested=weather_requested,
        weather_intent=user_has_weather_intent,
        document_intent=user_has_document_intent,
        history_mentions_weather=history_mentions_weather,
    )

    weather_result: WeatherToolOutput | None = None
    if weather_requested:
        weather_result = get_weather(extract_date_or_default(payload.message))
        weather_status = "ok" if weather_result.ok else (weather_result.error_type or "error")
        WEATHER_TOOL_CALLS_TOTAL.labels(status=weather_status).inc()

    documents = _retrieve_documents(payload.message) if rag_used else []
    logger.info(
        "rag_chunks_retrieved",
        session_id=str(session_id),
        rag_used=rag_used,
        chunk_count=len(documents),
        chunks=[_serialize_chunk_for_audit(document) for document in documents],
    )
    prompt = build_chat_prompt(
        user_message=payload.message,
        history=stored_history,
        context=format_context(documents),
        weather=weather_result,
    )
    system_instruction = (
        "Actua como guia turistico fiable de Tenerife. "
        "No inventes datos y resume con claridad."
    )
    logger.info(
        "chat_llm_prompt_prepared",
        session_id=str(session_id),
        model=generation_model_name,
        system_instruction=system_instruction,
        llm_prompt=prompt,
    )

    llm_started = perf_counter()
    response = get_chat_client().invoke(
        [
            SystemMessage(
                content=system_instruction
            ),
            HumanMessage(content=prompt),
        ]
    )
    llm_elapsed = perf_counter() - llm_started
    answer = str(response.content).strip()
    sources = format_sources(documents) if rag_used else []
    token_usage = extract_token_usage(response)
    logger.info(
        "chat_llm_completed",
        session_id=str(session_id),
        model=generation_model_name,
        latency_seconds=round(llm_elapsed, 4),
        input_tokens=token_usage["input_tokens"],
        output_tokens=token_usage["output_tokens"],
        total_tokens=token_usage["total_tokens"],
        answer=answer,
    )

    metadata = {
        "rag_used": rag_used,
        "weather_used": bool(weather_result),
        "source_count": len(sources),
        "token_usage": token_usage,
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
    CHAT_SOURCE_COUNT.observe(len(sources))
    LLM_REQUESTS_TOTAL.labels(model=generation_model_name).inc()
    LLM_INPUT_TOKENS_TOTAL.labels(model=generation_model_name).inc(
        token_usage["input_tokens"]
    )
    LLM_OUTPUT_TOKENS_TOTAL.labels(model=generation_model_name).inc(
        token_usage["output_tokens"]
    )
    LLM_TOTAL_TOKENS_TOTAL.labels(model=generation_model_name).inc(
        token_usage["total_tokens"]
    )
    LLM_REQUEST_DURATION_SECONDS.labels(model=generation_model_name).observe(
        llm_elapsed
    )

    return ChatResponse(
        session_id=str(session_id),
        answer=answer,
        sources=sources,
        weather=weather_result,
        rag_used=rag_used,
        created_at=created_at,
        metadata=metadata,
    )
