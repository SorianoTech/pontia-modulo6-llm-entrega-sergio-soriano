from __future__ import annotations

from pgvector.psycopg import register_vector

from app.core.config import get_settings
from app.db.connection import get_db_connection


def bootstrap_database() -> None:
    """Create required extensions, tables, and indexes for the application database."""
    settings = get_settings()
    with get_db_connection(register_vector_type=False) as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(connection)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    source_name TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id BIGSERIAL PRIMARY KEY,
                    chunk_key TEXT NOT NULL UNIQUE,
                    source_name TEXT NOT NULL REFERENCES documents(source_name) ON DELETE CASCADE,
                    chunk_id INTEGER NOT NULL,
                    page INTEGER,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding VECTOR({settings.embedding_dimensions}) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id UUID PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id BIGSERIAL PRIMARY KEY,
                    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chunks_source_name
                ON chunks (source_name)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id
                ON chat_messages (session_id, created_at)
                """
            )
            if settings.embedding_dimensions <= 2000:
                cursor.execute(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_indexes
                            WHERE schemaname = 'public'
                              AND indexname = 'idx_chunks_embedding_hnsw'
                        ) THEN
                            EXECUTE
                                'CREATE INDEX idx_chunks_embedding_hnsw ON chunks '
                                'USING hnsw (embedding vector_cosine_ops)';
                        END IF;
                    END
                    $$;
                    """
                )
