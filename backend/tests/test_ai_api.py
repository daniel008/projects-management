from pathlib import Path

from fastapi.testclient import TestClient

from app.ai_client import AIConfig, OpenRouterClient
from app.ai_service import AIService
from app.main import create_app


class StubAIService:
    def check_connectivity(self):
        return {
            "success": True,
            "status": "success",
            "provider": "openrouter",
            "model": "openai/gpt-oss-120b",
            "assistantMessage": "4",
            "error": None,
        }


def test_connectivity_endpoint_returns_normalized_payload(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            static_dir=tmp_path / "missing",
            db_path=tmp_path / "pm.db",
            ai_service=StubAIService(),
        )
    )

    response = client.get("/api/ai/connectivity")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "success",
        "provider": "openrouter",
        "model": "openai/gpt-oss-120b",
        "assistantMessage": "4",
        "error": None,
    }


def test_connectivity_endpoint_returns_clear_skip_message_when_key_missing(
    tmp_path: Path,
) -> None:
    config = AIConfig(
        api_key=None,
        model="openai/gpt-oss-120b",
        base_url="https://example.test/api/v1",
        timeout_seconds=8.0,
        max_retries=1,
        retry_backoff_seconds=0.05,
        temperature=0.0,
        max_tokens=64,
    )
    service = AIService(OpenRouterClient(config))

    client = TestClient(
        create_app(
            static_dir=tmp_path / "missing",
            db_path=tmp_path / "pm.db",
            ai_service=service,
        )
    )

    response = client.get("/api/ai/connectivity")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "skipped"
    assert "OPENROUTER_API_KEY" in body["error"]
