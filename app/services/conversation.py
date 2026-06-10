from __future__ import annotations

import re
from dataclasses import dataclass

WEATHER_PATTERN = re.compile(
    r"\b(tiempo|clima|temperatura|lluvia|viento|weather)\b",
    re.IGNORECASE,
)
DOCUMENT_PATTERN = re.compile(
    (
        r"\b(playa|teide|laguna|santa cruz|puerto de la cruz|que ver|qué ver|"
        r"ruta|restaurante|comer|museo|pueblo|guia|guía)\b"
    ),
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2}|hoy|mañana|manana)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class StoredMessage:
    role: str
    content: str


def trim_history(
    messages: list[StoredMessage],
    max_messages: int = 12,
    max_chars: int = 7000,
) -> list[StoredMessage]:
    trimmed = messages[-max_messages:]
    total_chars = sum(len(message.content) for message in trimmed)

    while len(trimmed) > 2 and total_chars > max_chars:
        trimmed.pop(0)
        total_chars = sum(len(message.content) for message in trimmed)

    return trimmed


def weather_intent(text: str) -> bool:
    return bool(WEATHER_PATTERN.search(text))


def has_document_intent(text: str) -> bool:
    return bool(DOCUMENT_PATTERN.search(text))


def extract_date_or_default(text: str) -> str:
    match = DATE_PATTERN.search(text)
    return match.group(1) if match else "hoy"


def serialize_history(messages: list[StoredMessage]) -> str:
    if not messages:
        return "Sin historial previo."

    return "\n".join(f"{message.role}: {message.content}" for message in messages)
