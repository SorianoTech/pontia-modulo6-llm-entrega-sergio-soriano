from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings_client() -> Any:
    """Build and cache the embeddings client used for document indexing and retrieval."""
    settings = get_settings()
    if settings.embedding_provider == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model,
            google_api_key=settings.google_api_key,
        )
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
    raise RuntimeError(f"Proveedor de embeddings no soportado: {settings.embedding_provider}")


@lru_cache(maxsize=1)
def get_chat_client() -> Any:
    """Build and cache the chat model client used to answer user questions."""
    settings = get_settings()
    if settings.generation_provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.generation_model,
            temperature=settings.generation_temperature,
            max_output_tokens=settings.generation_max_tokens,
            google_api_key=settings.google_api_key,
        )
    if settings.generation_provider == "ollama":
        return ChatOllama(
            model=settings.generation_model,
            base_url=settings.ollama_base_url,
            temperature=settings.generation_temperature,
            num_predict=settings.generation_max_tokens,
        )
    raise RuntimeError(f"Proveedor de generación no soportado: {settings.generation_provider}")


def get_generation_model_name() -> str:
    """Return the configured generation model name for logs and metrics."""
    return get_settings().generation_model


def require_embedding_configuration() -> None:
    """Validate that the embedding provider has the required runtime configuration."""
    settings = get_settings()
    if settings.embedding_provider == "gemini" and not settings.google_api_key:
        raise RuntimeError("Falta GOOGLE_API_KEY para usar embeddings con Gemini.")
    if settings.embedding_provider == "ollama" and not settings.ollama_base_url:
        raise RuntimeError("Falta OLLAMA_BASE_URL para usar embeddings con Ollama.")


def require_generation_configuration() -> None:
    """Validate that the generation provider has the required runtime configuration."""
    settings = get_settings()
    if settings.generation_provider == "gemini" and not settings.google_api_key:
        raise RuntimeError("Falta GOOGLE_API_KEY para usar generación con Gemini.")
    if settings.generation_provider == "ollama" and not settings.ollama_base_url:
        raise RuntimeError("Falta OLLAMA_BASE_URL para usar generación con Ollama.")
