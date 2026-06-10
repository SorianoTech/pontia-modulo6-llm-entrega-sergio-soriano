from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings_client() -> GoogleGenerativeAIEmbeddings:
    """Build and cache the embeddings client used for document indexing and retrieval."""
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )


@lru_cache(maxsize=1)
def get_chat_client() -> ChatGoogleGenerativeAI:
    """Build and cache the chat model client used to answer user questions."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.generation_model,
        temperature=settings.generation_temperature,
        max_output_tokens=settings.generation_max_tokens,
        google_api_key=settings.google_api_key,
    )
