from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central application settings loaded from `.env` and environment variables."""

    app_name: str = "Tenerife RAG App"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    streamlit_api_url: str = "http://127.0.0.1:8000"
    streamlit_server_port: int = 8501
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    generation_model: str = "gemini-2.5-flash-lite"
    embedding_model: str = "models/gemini-embedding-001"
    generation_temperature: float = 0.2
    generation_max_tokens: int = 1024
    rag_top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_dimensions: int = 3072
    request_timeout_seconds: int = 15
    database_url: str = "postgresql://postgres:postgres@localhost:5432/tenerife_app"
    data_pdf_path: Path = PROJECT_ROOT / "data" / "TENERIFE.pdf"
    audit_log_path: Path = PROJECT_ROOT / "logs" / "app.jsonl"
    auto_ingest_on_startup: bool = True
    weather_location: str = "Tenerife"
    open_meteo_geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"

    model_config = SettingsConfigDict(
        env_file=(".env", "notebook/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """Prioritize explicit init values and `.env` entries over shell environment variables."""
        return init_settings, dotenv_settings, env_settings, file_secret_settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance shared across the application."""
    return Settings()
