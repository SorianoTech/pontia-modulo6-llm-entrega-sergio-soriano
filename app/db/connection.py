from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg import Connection, connect
from psycopg.rows import dict_row

from app.core.config import get_settings


@contextmanager
def get_db_connection() -> Iterator[Connection]:
    settings = get_settings()
    connection = connect(
        settings.database_url,
        autocommit=True,
        row_factory=dict_row,
    )
    register_vector(connection)
    try:
        yield connection
    finally:
        connection.close()
