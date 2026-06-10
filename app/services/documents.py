from __future__ import annotations

import hashlib
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


def file_sha256(path: Path) -> str:
    """Compute a stable checksum for a source file used during idempotent ingestion."""
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pdf_documents(path: Path) -> list[Document]:
    """Load the Tenerife PDF as LangChain documents enriched with page metadata."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el PDF en {path}")

    reader = PdfReader(str(path))
    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages):
        page_content = page.extract_text() or ""
        documents.append(
            Document(
                page_content=page_content,
                metadata={
                    "source_name": path.name,
                    "source_path": str(path),
                    "page": page_number,
                    "page_label": str(page_number + 1),
                    "total_pages": len(reader.pages),
                },
            )
        )

    return documents


def split_documents(
    documents: list[Document],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Split source pages into retrievable chunks and assign sequential chunk identifiers."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)

    for chunk_id, document in enumerate(chunks):
        document.metadata["chunk_id"] = chunk_id

    return chunks
