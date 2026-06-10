from fastapi.testclient import TestClient

from app.main import create_app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(create_app(run_startup_tasks=False))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_html_page() -> None:
    client = TestClient(create_app(run_startup_tasks=False))

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Descubre Tenerife con un chat RAG" in response.text
