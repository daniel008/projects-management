from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable

import httpx

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-oss-120b"


@dataclass(frozen=True)
class AIConfig:
    api_key: str | None
    model: str
    base_url: str
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float
    temperature: float
    max_tokens: int

    @classmethod
    def from_env(cls) -> "AIConfig":
        return cls(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            base_url=os.getenv("OPENROUTER_BASE_URL",
                               DEFAULT_OPENROUTER_BASE_URL),
            timeout_seconds=float(
                os.getenv("OPENROUTER_TIMEOUT_SECONDS", "15")),
            max_retries=int(os.getenv("OPENROUTER_MAX_RETRIES", "2")),
            retry_backoff_seconds=float(
                os.getenv("OPENROUTER_RETRY_BACKOFF_SECONDS", "0.3")
            ),
            temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0")),
            max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "64")),
        )


class OpenRouterClient:
    def __init__(
        self,
        config: AIConfig,
        http_client: httpx.Client | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self._http_client = http_client or httpx.Client()
        self._sleep_fn = sleep_fn

    def is_configured(self) -> bool:
        return bool(self.config.api_key)

    def request_text(self, prompt: str) -> str:
        return self.request_messages([{"role": "user", "content": prompt}])

    def request_messages(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
    ) -> str:
        if not self.is_configured():
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._http_client.post(
                    f"{self.config.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout_seconds,
                )
                response.raise_for_status()
                return self._parse_response_text(response)
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError,
                ValueError,
                KeyError,
                TypeError,
            ) as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                backoff_seconds = self.config.retry_backoff_seconds * \
                    (2**attempt)
                self._sleep_fn(backoff_seconds)

        raise RuntimeError(
            "OpenRouter request failed after configured retries.") from last_error

    def _parse_response_text(self, response: httpx.Response) -> str:
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, list):
            parts = [
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            content = "\n".join(part for part in parts if part)

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "OpenRouter response did not contain assistant text.")

        return content.strip()
