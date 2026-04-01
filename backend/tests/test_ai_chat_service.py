import json

from app.ai_client import AIConfig, OpenRouterClient
from app.ai_service import AIService
from app.schemas import AIChatRequest, ChatMessage


def make_service() -> AIService:
    config = AIConfig(
        api_key="test-key",
        model="openai/gpt-oss-120b",
        base_url="https://example.test/api/v1",
        timeout_seconds=8.0,
        max_retries=0,
        retry_backoff_seconds=0.01,
        temperature=0.0,
        max_tokens=256,
    )
    return AIService(OpenRouterClient(config))


def test_build_chat_messages_contains_board_question_and_history() -> None:
    service = make_service()
    board = {
        "columns": [{"id": "col-a", "title": "Todo", "cardIds": ["card-1"]}],
        "cards": {"card-1": {"id": "card-1", "title": "T", "details": "D"}},
    }
    request = AIChatRequest(
        question="Move card-1 to done",
        history=[ChatMessage(role="user", content="hello")],
    )

    messages = service._build_chat_messages(board, request)

    assert messages[0]["role"] == "system"
    assert "userMessage" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    payload = json.loads(messages[1]["content"])
    assert payload["question"] == "Move card-1 to done"
    assert payload["history"][0]["content"] == "hello"
    assert payload["board"]["cards"]["card-1"]["id"] == "card-1"


def test_parse_structured_response_accepts_valid_json_with_board() -> None:
    service = make_service()

    message, board = service._parse_structured_response(
        '{"userMessage":"Done","board":{"columns":[],"cards":{}}}'
    )

    assert message == "Done"
    assert board == {"columns": [], "cards": {}}


def test_parse_structured_response_handles_partial_json() -> None:
    service = make_service()

    message, board = service._parse_structured_response(
        '{"assistantMessage":"Ack"}')

    assert message == "Ack"
    assert board is None


def test_parse_structured_response_handles_invalid_json_with_fallback_message() -> None:
    service = make_service()

    message, board = service._parse_structured_response(
        "I could not produce valid JSON")

    assert message == "I could not produce valid JSON"
    assert board is None


def test_parse_structured_response_accepts_markdown_fenced_json() -> None:
    service = make_service()

    message, board = service._parse_structured_response(
        """```json
{"userMessage":"Moved card","board":{"columns":[],"cards":{}}}
```"""
    )

    assert message == "Moved card"
    assert board == {"columns": [], "cards": {}}


def test_parse_structured_response_recovers_message_from_truncated_json() -> None:
    service = make_service()

    message, board = service._parse_structured_response(
        '{"userMessage":"Renamed card-1","board":{"columns":[{"id":"col-backlog"'
    )

    assert message == "Renamed card-1"
    assert board is None


def test_parse_structured_response_recovers_message_from_pretty_truncated_json() -> None:
    service = make_service()

    message, board = service._parse_structured_response(
        '{\n  "userMessage": "Moved card-1 to Review",\n  "board": {\n    "columns": ['
    )

    assert message == "Moved card-1 to Review"
    assert board is None
