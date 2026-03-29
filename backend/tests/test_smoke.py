from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_serves_html_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello from FastAPI" in response.text
    assert "/api/hello" in response.text


def test_hello_api_returns_expected_payload() -> None:
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world", "service": "backend"}


def test_healthz_returns_ok() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
