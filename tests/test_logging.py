import json
import logging

from app.core.logging import configure_logging, get_logger
from app.services.chat import _serialize_chunk_for_audit


def test_configure_logging_writes_json_lines_to_audit_file(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "audit.jsonl"
    settings = type("Settings", (), {"audit_log_path": log_path})()
    monkeypatch.setattr("app.core.logging.get_settings", lambda: settings)

    configure_logging()
    logging.getLogger("uvicorn.access").info("noise_event")
    get_logger("app.tests.audit").info("audit_event", key="value")

    for handler in logging.getLogger().handlers:
        handler.flush()

    payload = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert payload["event"] == "audit_event"
    assert payload["key"] == "value"
    assert payload["level"] == "info"


def test_serialize_chunk_for_audit_returns_compact_chunk_fields() -> None:
    serialized = _serialize_chunk_for_audit(
        {
            "chunk_key": "TENERIFE.pdf:4",
            "source_name": "TENERIFE.pdf",
            "chunk_id": 4,
            "page": 2,
            "similarity": 0.98765,
            "metadata": {"page_label": "3"},
        }
    )

    assert serialized == {
        "chunk_key": "TENERIFE.pdf:4",
        "source_name": "TENERIFE.pdf",
        "chunk_id": 4,
        "page": 2,
        "page_label": "3",
        "similarity": 0.9877,
    }
