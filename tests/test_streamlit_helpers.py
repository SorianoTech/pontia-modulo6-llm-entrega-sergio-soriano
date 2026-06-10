from app.ui.streamlit_helpers import build_api_url, format_sources


def test_build_api_url_joins_base_and_path() -> None:
    assert build_api_url("http://127.0.0.1:8000", "/api/v1/chat") == "http://127.0.0.1:8000/api/v1/chat"


def test_format_sources_returns_human_readable_text() -> None:
    value = format_sources(
        [
            {"source": "TENERIFE.pdf", "page": 2, "chunk_id": 8},
            {"source": "TENERIFE.pdf", "page": 5, "chunk_id": 12},
        ]
    )

    assert value == "TENERIFE.pdf p.2 ch.8 | TENERIFE.pdf p.5 ch.12"
