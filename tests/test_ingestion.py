from langchain_core.documents import Document

from app.services.ingestion import build_chunk_rows


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

