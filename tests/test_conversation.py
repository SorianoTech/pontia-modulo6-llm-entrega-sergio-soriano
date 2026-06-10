from app.services.conversation import (
    StoredMessage,
    extract_date_or_default,
    has_document_intent,
    trim_history,
    weather_intent,
)


def test_trim_history_respects_limits() -> None:
    messages = [StoredMessage(role="user", content=f"mensaje {index}") for index in range(20)]

    trimmed = trim_history(messages, max_messages=5, max_chars=100)

    assert len(trimmed) == 5
    assert trimmed[0].content == "mensaje 15"


def test_weather_intent_detects_weather_queries() -> None:
    assert weather_intent("Que tiempo hara hoy en Tenerife?")
    assert not weather_intent("Que ver en La Laguna?")


def test_has_document_intent_detects_tourism_queries() -> None:
    assert has_document_intent("Que ver en Puerto de la Cruz?")
    assert not has_document_intent("Necesito una prediccion del clima")


def test_extract_date_or_default_uses_today_when_missing() -> None:
    assert extract_date_or_default("Que tiempo hara?") == "hoy"
    assert extract_date_or_default("Y mañana?") == "mañana"

