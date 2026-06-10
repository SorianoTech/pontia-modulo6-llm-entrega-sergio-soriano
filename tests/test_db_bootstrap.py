from contextlib import contextmanager

from app.db import bootstrap
from app.db.connection import get_db_connection


class FakeCursor:
    def __init__(self) -> None:
        self.executed_statements: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, statement: str) -> None:
        self.executed_statements.append(statement)


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True


def test_get_db_connection_skips_register_vector_when_disabled(monkeypatch) -> None:
    fake_connection = FakeConnection()
    register_calls: list[FakeConnection] = []

    monkeypatch.setattr(
        "app.db.connection.get_settings",
        lambda: type("Settings", (), {"database_url": "postgresql://test"})(),
    )
    monkeypatch.setattr("app.db.connection.connect", lambda *args, **kwargs: fake_connection)
    monkeypatch.setattr(
        "app.db.connection.register_vector",
        lambda connection: register_calls.append(connection),
    )

    with get_db_connection(register_vector_type=False) as connection:
        assert connection is fake_connection

    assert register_calls == []
    assert fake_connection.closed is True


def test_bootstrap_creates_extension_before_registering_vector(monkeypatch) -> None:
    fake_connection = FakeConnection()
    register_events: list[str] = []
    requested_flags: list[bool] = []

    monkeypatch.setattr(
        bootstrap,
        "get_settings",
        lambda: type("Settings", (), {"embedding_dimensions": 3072})(),
    )

    @contextmanager
    def fake_get_db_connection(register_vector_type: bool = True):
        requested_flags.append(register_vector_type)
        yield fake_connection

    def fake_register_vector(connection) -> None:
        assert connection is fake_connection
        register_events.append("registered")

    monkeypatch.setattr(bootstrap, "get_db_connection", fake_get_db_connection)
    monkeypatch.setattr(bootstrap, "register_vector", fake_register_vector)

    bootstrap.bootstrap_database()

    assert requested_flags == [False]
    assert (
        fake_connection.cursor_instance.executed_statements[0]
        == "CREATE EXTENSION IF NOT EXISTS vector"
    )
    assert register_events == ["registered"]


def test_bootstrap_skips_hnsw_index_for_high_dimensional_embeddings(monkeypatch) -> None:
    fake_connection = FakeConnection()

    monkeypatch.setattr(
        bootstrap,
        "get_settings",
        lambda: type("Settings", (), {"embedding_dimensions": 3072})(),
    )

    @contextmanager
    def fake_get_db_connection(register_vector_type: bool = True):
        yield fake_connection

    monkeypatch.setattr(bootstrap, "get_db_connection", fake_get_db_connection)
    monkeypatch.setattr(bootstrap, "register_vector", lambda connection: None)

    bootstrap.bootstrap_database()

    assert not any(
        "idx_chunks_embedding_hnsw" in statement
        for statement in fake_connection.cursor_instance.executed_statements
    )
