from __future__ import annotations

from app.models.schemas import SourceReference, WeatherToolOutput
from app.services.conversation import StoredMessage, serialize_history


def format_sources(documents: list[dict]) -> list[SourceReference]:
    return [
        SourceReference(
            source=document["source_name"],
            page=document.get("page"),
            chunk_id=document.get("chunk_id"),
        )
        for document in documents
    ]


def format_context(documents: list[dict]) -> str:
    if not documents:
        return "No hay contexto documental recuperado."

    blocks: list[str] = []
    for index, document in enumerate(documents, start=1):
        blocks.append(
            f"[Fuente {index}: {document['source_name']}, pagina {document.get('page', '?')}, "
            f"chunk {document.get('chunk_id', '?')}]\n{document['content']}"
        )
    return "\n\n".join(blocks)


def build_chat_prompt(
    user_message: str,
    history: list[StoredMessage],
    context: str,
    weather: WeatherToolOutput | None,
) -> str:
    weather_block = "Sin datos meteorologicos."
    if weather and weather.ok and weather.data:
        data = weather.data
        weather_block = (
            f"Clima consultado para {data.fecha} en {data.ubicacion}: "
            f"min {data.temperatura_min_c} C, max {data.temperatura_max_c} C, "
            f"condicion {data.condicion}. Fuente: {data.fuente}."
        )
    elif weather and not weather.ok:
        weather_block = f"La consulta meteorologica fallo: {weather.error}"

    return (
        "Eres un guia turistico experto en Tenerife.\n"
        "Responde siempre en espanol.\n"
        "Usa solo el contexto documental recuperado y el bloque meteorologico cuando existan.\n"
        "Si no hay suficiente informacion documental para responder una pregunta "
        "de la guia, dilo con claridad.\n"
        "Si usas contexto documental, termina con una linea de fuentes.\n\n"
        f"Historial:\n{serialize_history(history)}\n\n"
        f"Contexto documental:\n{context}\n\n"
        f"Bloque meteorologico:\n{weather_block}\n\n"
        f"Pregunta del usuario:\n{user_message}"
    )
