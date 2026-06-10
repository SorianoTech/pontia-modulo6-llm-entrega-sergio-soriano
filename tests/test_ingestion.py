from langchain_core.documents import Document

from app.services.ingestion import build_chunk_rows, ingest_pdf


def test_build_chunk_rows_generates_stable_keys() -> None:
    chunks = [
        Document(
            page_content="contenido 1",
            metadata={"chunk_id": 0, "page": 0, "source_name": "TENERIFE.pdf"},
        ),
        Document(
            page_content="contenido 2",
            metadata={"chunk_id": 1, "page": 1, "source_name": "TENERIFE.pdf"},
        ),
    ]

    rows = build_chunk_rows("TENERIFE.pdf", chunks, [[0.1, 0.2], [0.3, 0.4]])

    assert rows[0][0] == "TENERIFE.pdf:0"
    assert rows[1][2] == 1
    assert rows[1][4] == "contenido 2"


def test_ingest_pdf_reuses_existing_index_when_checksum_matches(monkeypatch) -> None:
    fake_path = type("Path", (), {"name": "TENERIFE.pdf"})()
    settings = type("Settings", (), {"data_pdf_path": fake_path})()

    monkeypatch.setattr("app.services.ingestion.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.ingestion.bootstrap_database", lambda: None)
    monkeypatch.setattr("app.services.ingestion.file_sha256", lambda path: "same-checksum")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr("app.services.ingestion.get_db_connection", lambda: FakeConnection())
    monkeypatch.setattr(
        "app.services.ingestion.get_document",
        lambda connection, source_name: {
            "checksum": "same-checksum",
            "metadata": {"total_pages": 25},
        },
    )
    monkeypatch.setattr("app.services.ingestion.count_chunks", lambda connection, source_name: 46)

    result = ingest_pdf(force_reindex=False)

    assert result["source_name"] == "TENERIFE.pdf"
    assert result["chunks"] == 46
    assert result["pages"] == 25
    assert result["reused_existing_index"] is True
