from pgvector import Vector

from app.db.repositories import search_similar_chunks


class FakeCursor:
    def __init__(self) -> None:
        self.executed_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, statement, params) -> None:
        self.executed_params = params

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


def test_search_similar_chunks_casts_query_embedding_to_vector() -> None:
    connection = FakeConnection()

    search_similar_chunks(connection, [0.1, 0.2], 3)

    assert isinstance(connection.cursor_instance.executed_params[0], Vector)
    assert isinstance(connection.cursor_instance.executed_params[1], Vector)
    assert connection.cursor_instance.executed_params[2] == 3

