from __future__ import annotations

from datetime import datetime
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from app.services.conversation import StoredMessage


def upsert_document(
    connection: Connection,
    *,
    source_name: str,
    source_path: str,
    checksum: str,
    metadata: dict,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO documents (source_name, source_path, checksum, metadata)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (source_name) DO UPDATE
            SET source_path = EXCLUDED.source_path,
                checksum = EXCLUDED.checksum,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """,
            (source_name, source_path, checksum, Jsonb(metadata)),
        )


def delete_chunks_for_source(connection: Connection, source_name: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM chunks WHERE source_name = %s", (source_name,))


def insert_chunks(connection: Connection, rows: list[tuple]) -> None:
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO chunks (
                chunk_key,
                source_name,
                chunk_id,
                page,
                content,
                metadata,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )


def get_document(connection: Connection, source_name: str) -> dict | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT source_name, source_path, checksum, metadata
            FROM documents
            WHERE source_name = %s
            """,
            (source_name,),
        )
        row = cursor.fetchone()
    return None if row is None else dict(row)


def count_chunks(connection: Connection, source_name: str | None = None) -> int:
    with connection.cursor() as cursor:
        if source_name:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM chunks WHERE source_name = %s",
                (source_name,),
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM chunks")
        row = cursor.fetchone()
    return int(row["total"])


def search_similar_chunks(connection: Connection, embedding: list[float], limit: int) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                chunk_key,
                source_name,
                chunk_id,
                page,
                content,
                metadata,
                1 - (embedding <=> %s) AS similarity
            FROM chunks
            ORDER BY embedding <=> %s
            LIMIT %s
            """,
            (embedding, embedding, limit),
        )
        rows = cursor.fetchall()
    return list(rows)


def create_session(connection: Connection, session_id: UUID) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_sessions (id)
            VALUES (%s)
            ON CONFLICT (id) DO UPDATE
            SET updated_at = NOW()
            """,
            (session_id,),
        )


def append_chat_message(
    connection: Connection,
    *,
    session_id: UUID,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> None:
    payload = metadata or {}
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, role, content, Jsonb(payload)),
        )
        cursor.execute(
            "UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s",
            (session_id,),
        )


def list_recent_messages(
    connection: Connection,
    *,
    session_id: UUID,
    limit: int = 12,
) -> list[StoredMessage]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (session_id, limit),
        )
        rows = cursor.fetchall()

    ordered_rows = reversed(rows)
    return [StoredMessage(role=row["role"], content=row["content"]) for row in ordered_rows]


def latest_message_timestamp(connection: Connection, session_id: UUID) -> datetime | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (session_id,),
        )
        row = cursor.fetchone()
    return None if row is None else row["created_at"]
