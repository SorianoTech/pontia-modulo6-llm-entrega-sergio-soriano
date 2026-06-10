import pytest

from app.services.weather import normalize_iso_date, weather_code_to_text


def test_normalize_iso_date_accepts_iso_format() -> None:
    assert normalize_iso_date("2026-06-12") == "2026-06-12"


def test_normalize_iso_date_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        normalize_iso_date("2026-15-99")


def test_weather_code_to_text_returns_fallback_for_unknown_code() -> None:
    assert weather_code_to_text(999) == "codigo meteorologico 999"

