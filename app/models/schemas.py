from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Reference to a retrieved document chunk used to ground a response."""

    source: str
    page: int | None = None
    chunk_id: int | None = None


class WeatherResult(BaseModel):
    """Normalized weather payload returned by the Open-Meteo integration."""

    fecha: str
    ubicacion: str
    temperatura_min_c: float | None = None
    temperatura_max_c: float | None = None
    condicion: str
    weather_code: int | None = None
    latitud: float
    longitud: float
    timezone: str
    fuente: str


class WeatherToolOutput(BaseModel):
    """Outcome of a weather tool call, including errors when the lookup fails."""

    ok: bool
    data: WeatherResult | None = None
    error_type: str | None = None
    error: str | None = None
    help: str | None = None


class ChatRequest(BaseModel):
    """Payload accepted by the chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Structured response returned to the Streamlit client and API consumers."""

    session_id: str
    answer: str
    sources: list[SourceReference]
    weather: WeatherToolOutput | None = None
    rag_used: bool
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class InfoCard(BaseModel):
    """Short content block rendered on the Streamlit landing view."""

    title: str
    description: str
