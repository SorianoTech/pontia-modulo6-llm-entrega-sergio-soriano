from __future__ import annotations

from typing import Any


def extract_token_usage(message: Any) -> dict[str, int]:
    """Normalize token accounting across different LangChain response metadata shapes."""
    usage = getattr(message, "usage_metadata", {}) or {}
    response_metadata = getattr(message, "response_metadata", {}) or {}
    token_usage = (
        response_metadata.get("token_usage", {})
        if isinstance(response_metadata, dict)
        else {}
    )

    input_tokens = (
        usage.get("input_tokens")
        or token_usage.get("prompt_token_count")
        or token_usage.get("input_tokens")
        or 0
    )
    output_tokens = (
        usage.get("output_tokens")
        or token_usage.get("candidates_token_count")
        or token_usage.get("output_tokens")
        or 0
    )
    total_tokens = (
        usage.get("total_tokens")
        or token_usage.get("total_token_count")
        or (input_tokens + output_tokens)
    )

    return {
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
        "total_tokens": int(total_tokens),
    }
