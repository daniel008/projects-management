import json

import httpx

from app.ai_client import AIConfig, OpenRouterClient
from app.ai_service import AIService


def test_ai_config_defaults_to_expected_model(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("OPENROUTER_MAX_RETRIES", raising=False)

    config = AIConfig.from_env()

    assert config.model == "openai/gpt-oss-120b"
    assert config.timeout_seconds == 15.0
    assert config.max_retries == 2


def test_openrouter_client_composes_request_and_parses_response() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("Authorization")
        captured["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"choices": [{"message": {"content": "4"}}]})

    config = AIConfig(
        api_key="test-key",
        model="openai/gpt-oss-120b",
        base_url="https://example.test/api/v1",
        timeout_seconds=8.0,
        max_retries=0,
        retry_backoff_seconds=0.01,
        temperature=0.0,
        max_tokens=64,
    )
    client = OpenRouterClient(
        config,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.request_text("What is 2+2?")

    assert result == "4"
    assert captured["url"] == "https://example.test/api/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "openai/gpt-oss-120b"
    assert payload["messages"][0]["content"] == "What is 2+2?"
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 64


def test_openrouter_client_retries_on_timeout_then_succeeds() -> None:
    calls = 0
    sleep_calls: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("read timeout", request=request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "4"}}]})

    config = AIConfig(
        api_key="test-key",
        model="openai/gpt-oss-120b",
        base_url="https://example.test/api/v1",
        timeout_seconds=8.0,
        max_retries=1,
        retry_backoff_seconds=0.05,
        temperature=0.0,
        max_tokens=64,
    )
    client = OpenRouterClient(
        config,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep_fn=lambda seconds: sleep_calls.append(seconds),
    )

    result = client.request_text("Return 4")

    assert result == "4"
    assert calls == 2
    assert sleep_calls == [0.05]


def test_ai_service_returns_skipped_status_when_api_key_missing() -> None:
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
    result = service.check_connectivity()

    assert result.success is False
    assert result.status == "skipped"
    assert "OPENROUTER_API_KEY" in (result.error or "")
