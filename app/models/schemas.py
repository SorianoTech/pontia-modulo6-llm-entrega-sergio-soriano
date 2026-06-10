from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    source: str
    page: int | None = None
    chunk_id: int | None = None


class WeatherResult(BaseModel):
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
    ok: bool
    data: WeatherResult | None = None
    error_type: str | None = None
    error: str | None = None
    help: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceReference]
    weather: WeatherToolOutput | None = None
    rag_used: bool
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class InfoCard(BaseModel):
    title: str
    description: str

