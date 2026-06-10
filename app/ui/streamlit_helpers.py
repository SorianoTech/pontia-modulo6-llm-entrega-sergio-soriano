from __future__ import annotations

from urllib.parse import urljoin


def build_api_url(base_url: str, path: str) -> str:
    normalized_base = base_url.rstrip("/") + "/"
    normalized_path = path.lstrip("/")
    return urljoin(normalized_base, normalized_path)


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return ""

    return " | ".join(
        f"{source['source']} p.{source.get('page', '?')} ch.{source.get('chunk_id', '?')}"
        for source in sources
    )

