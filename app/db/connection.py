from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg import Connection, connect
from psycopg.rows import dict_row

from app.core.config import get_settings


@contextmanager
def get_db_connection(register_vector_type: bool = True) -> Iterator[Connection]:
    settings = get_settings()
    connection = connect(
        settings.database_url,
        autocommit=True,
        row_factory=dict_row,
    )
    if register_vector_type:
        register_vector(connection)
    try:
        yield connection
    finally:
        connection.close()
