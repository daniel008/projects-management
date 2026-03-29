from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app(static_dir=Path("__missing_static_dir__")))


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


def test_frontend_static_shell_is_served_when_available(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    static_client = TestClient(create_app(static_dir=tmp_path))
    response = static_client.get("/")
    assert response.status_code == 200
    assert "Kanban Studio" in response.text
