from fastapi.testclient import TestClient

from app.main import create_app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(create_app(run_startup_tasks=False, run_streamlit=False))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirects_to_streamlit() -> None:
    client = TestClient(create_app(run_startup_tasks=False, run_streamlit=False))

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver:8501"


def test_metrics_endpoint_returns_prometheus_payload() -> None:
    client = TestClient(create_app(run_startup_tasks=False, run_streamlit=False))

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
