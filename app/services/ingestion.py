from __future__ import annotations

from psycopg.types.json import Jsonb

from app.core.config import get_settings
from app.db.bootstrap import bootstrap_database
from app.db.connection import get_db_connection
from app.db.repositories import (
    count_chunks,
    delete_chunks_for_source,
    insert_chunks,
    upsert_document,
)
from app.services.documents import file_sha256, load_pdf_documents, split_documents
from app.services.llm import get_embeddings_client


def build_chunk_rows(source_name: str, chunks: list, embeddings: list[list[float]]) -> list[tuple]:
    rows: list[tuple] = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        metadata = dict(chunk.metadata)
        chunk_id = int(metadata["chunk_id"])
        rows.append(
            (
                f"{source_name}:{chunk_id}",
                source_name,
                chunk_id,
                metadata.get("page"),
                chunk.page_content,
                Jsonb(metadata),
                embedding,
            )
        )
    return rows


def ingest_pdf(force_reindex: bool = True) -> dict:
    settings = get_settings()
    bootstrap_database()

    documents = load_pdf_documents(settings.data_pdf_path)
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    embeddings_client = get_embeddings_client()
    embedding_vectors = embeddings_client.embed_documents([chunk.page_content for chunk in chunks])
    checksum = file_sha256(settings.data_pdf_path)

    with get_db_connection() as connection:
        upsert_document(
            connection,
            source_name=settings.data_pdf_path.name,
            source_path=str(settings.data_pdf_path),
            checksum=checksum,
            metadata={
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "total_pages": len(documents),
            },
        )
        if force_reindex:
            delete_chunks_for_source(connection, settings.data_pdf_path.name)

        insert_chunks(
            connection,
            build_chunk_rows(settings.data_pdf_path.name, chunks, embedding_vectors),
        )
        total_chunks = count_chunks(connection, settings.data_pdf_path.name)

    return {
        "source_name": settings.data_pdf_path.name,
        "pages": len(documents),
        "chunks": total_chunks,
        "checksum": checksum,
    }
