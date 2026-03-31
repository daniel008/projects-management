import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.ai_service import AIService
from app.main import create_app


class StubClient:
    def __init__(self, response_text: str, configured: bool = True) -> None:
        self._response_text = response_text
        self._configured = configured
        self.config = type("Config", (), {"model": "openai/gpt-oss-120b"})()

    def is_configured(self) -> bool:
        return self._configured

    def request_messages(self, messages: list[dict[str, str]]) -> str:
        return self._response_text


def make_client(tmp_path: Path, response_text: str) -> TestClient:
    ai_service = AIService(StubClient(response_text))
    return TestClient(
        create_app(
            static_dir=tmp_path / "missing",
            db_path=tmp_path / "pm.db",
            ai_service=ai_service,
        )
    )


def test_ai_chat_applies_valid_board_update_and_persists(tmp_path: Path) -> None:
    bootstrap_client = make_client(tmp_path, '{"userMessage":"noop"}')
    current_board = bootstrap_client.get("/api/board/alice").json()

    updated_board = json.loads(json.dumps(current_board))
    updated_board["cards"]["card-1"]["title"] = "Updated by AI"

    ai_response = json.dumps(
        {
            "userMessage": "Updated the card title.",
            "board": updated_board,
        }
    )
    client = make_client(tmp_path, ai_response)

    response = client.post(
        "/api/ai/chat/alice",
        json={"question": "Please update card-1", "history": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["assistantMessage"] == "Updated the card title."
    assert body["boardUpdated"] is True
    assert body["board"]["cards"]["card-1"]["title"] == "Updated by AI"

    verify = client.get("/api/board/alice")
    assert verify.status_code == 200
    assert verify.json()["cards"]["card-1"]["title"] == "Updated by AI"


def test_ai_chat_returns_message_when_output_is_not_structured(tmp_path: Path) -> None:
    client = make_client(tmp_path, "I suggest moving card-1 to review.")

    response = client.post(
        "/api/ai/chat/alice",
        json={"question": "What should I do next?", "history": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistantMessage"] == "I suggest moving card-1 to review."
    assert body["boardUpdated"] is False
    assert body["status"] == "success"
