from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the application.",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
CHAT_TURNS_TOTAL = Counter(
    "chat_turns_total",
    "Total processed chat turns.",
    ["rag_used", "weather_used"],
)
LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total LLM invocations.",
    ["model"],
)
LLM_INPUT_TOKENS_TOTAL = Counter(
    "llm_input_tokens_total",
    "Total input tokens sent to the LLM.",
    ["model"],
)
LLM_OUTPUT_TOKENS_TOTAL = Counter(
    "llm_output_tokens_total",
    "Total output tokens returned by the LLM.",
    ["model"],
)
LLM_TOTAL_TOKENS_TOTAL = Counter(
    "llm_total_tokens_total",
    "Total tokens used by the LLM.",
    ["model"],
)
LLM_REQUEST_DURATION_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds.",
    ["model"],
)
CHAT_SOURCE_COUNT = Histogram(
    "chat_source_count",
    "Number of retrieved source chunks used per chat response.",
    buckets=(0, 1, 2, 3, 4, 5, 8, 12),
)
WEATHER_TOOL_CALLS_TOTAL = Counter(
    "weather_tool_calls_total",
    "Total weather tool invocations.",
    ["status"],
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
