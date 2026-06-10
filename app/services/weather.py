from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache

import requests

from app.core.config import get_settings
from app.models.schemas import WeatherResult, WeatherToolOutput

WEATHER_CODE_MAP = {
    0: "despejado",
    1: "principalmente despejado",
    2: "parcialmente nublado",
    3: "cubierto",
    45: "niebla",
    48: "niebla con escarcha",
    51: "llovizna ligera",
    53: "llovizna moderada",
    55: "llovizna densa",
    56: "llovizna helada ligera",
    57: "llovizna helada densa",
    61: "lluvia ligera",
    63: "lluvia moderada",
    65: "lluvia intensa",
    80: "chubascos ligeros",
    81: "chubascos moderados",
    82: "chubascos violentos",
    95: "tormenta",
}


def normalize_iso_date(raw_date: str) -> str:
    value = (raw_date or "").strip().lower()
    today = datetime.now().date()

    if value in {"hoy", "today"}:
        return today.isoformat()
    if value in {"mañana", "manana", "tomorrow"}:
        return (today + timedelta(days=1)).isoformat()

    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(
            "Formato de fecha invalido. Usa YYYY-MM-DD, 'hoy' o 'mañana'."
        ) from exc


def weather_code_to_text(code: int | None) -> str:
    if code is None:
        return "condicion desconocida"
    return WEATHER_CODE_MAP.get(code, f"codigo meteorologico {code}")


@lru_cache(maxsize=8)
def geocode_location(location: str) -> dict:
    settings = get_settings()
    response = requests.get(
        settings.open_meteo_geocoding_url,
        params={
            "name": location,
            "count": 1,
            "language": "es",
            "format": "json",
        },
        timeout=settings.request_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results") or []
    if not results:
        raise RuntimeError(f"No se encontro ubicacion para '{location}'")

    top = results[0]
    return {
        "name": top.get("name", location),
        "country": top.get("country", ""),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
        "timezone": top.get("timezone", "auto"),
    }


def get_weather(raw_date: str) -> WeatherToolOutput:
    settings = get_settings()
    try:
        date_value = normalize_iso_date(raw_date)
        location = geocode_location(settings.weather_location)
        response = requests.get(
            settings.open_meteo_forecast_url,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": location["timezone"],
                "start_date": date_value,
                "end_date": date_value,
            },
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        daily = payload.get("daily") or {}
        dates = daily.get("time") or []
        if not dates:
            raise RuntimeError(
                "Open-Meteo no devolvio datos diarios para la fecha solicitada"
            )

        data = WeatherResult(
            fecha=dates[0],
            ubicacion=f"{location['name']}, {location['country']}".strip(", "),
            temperatura_min_c=(daily.get("temperature_2m_min") or [None])[0],
            temperatura_max_c=(daily.get("temperature_2m_max") or [None])[0],
            condicion=weather_code_to_text((daily.get("weathercode") or [None])[0]),
            weather_code=(daily.get("weathercode") or [None])[0],
            latitud=location["latitude"],
            longitud=location["longitude"],
            timezone=payload.get("timezone", location["timezone"]),
            fuente="open-meteo",
        )
        return WeatherToolOutput(ok=True, data=data)
    except ValueError as exc:
        return WeatherToolOutput(
            ok=False,
            error_type="validation_error",
            error=str(exc),
            help="Usa fecha en formato YYYY-MM-DD, o 'hoy'/'mañana'.",
        )
    except requests.RequestException as exc:
        return WeatherToolOutput(
            ok=False,
            error_type="api_error",
            error=f"Error HTTP con Open-Meteo: {exc}",
            help="No pude consultar Open-Meteo en este momento. Intenta de nuevo.",
        )
    except Exception as exc:  # noqa: BLE001
        return WeatherToolOutput(
            ok=False,
            error_type="runtime_error",
            error=str(exc),
            help="Intenta de nuevo en unos segundos.",
        )
