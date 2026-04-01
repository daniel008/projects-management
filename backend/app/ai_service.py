from __future__ import annotations

import json
import logging
import re
import time

from app.board_service import BoardService
from app.ai_client import OpenRouterClient
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIConnectivityResponse,
    BoardPayload,
)

logger = logging.getLogger(__name__)

CONNECTIVITY_PROMPT = "Return only the number 4. What is 2+2?"
CHAT_SYSTEM_PROMPT = (
    "You are a project assistant for a Kanban board. "
    "Return JSON with keys: userMessage (string), optional board (full board object). "
    "Do not include markdown code fences."
)
FALLBACK_MESSAGE = (
    "I could not apply a structured board update, but I can still help with planning next steps."
)
MIN_CHAT_MAX_TOKENS = 1200


class AIService:
    def __init__(self, client: OpenRouterClient) -> None:
        self.client = client

    def check_connectivity(self) -> AIConnectivityResponse:
        start = time.perf_counter()

        if not self.client.is_configured():
            result = AIConnectivityResponse(
                success=False,
                status="skipped",
                provider="openrouter",
                model=self.client.config.model,
                assistant_message=None,
                error="OPENROUTER_API_KEY is not configured. Connectivity check skipped.",
            )
            self._log_result(result, start)
            return result

        try:
            assistant_message = self.client.request_text(CONNECTIVITY_PROMPT)
            result = AIConnectivityResponse(
                success=True,
                status="success",
                provider="openrouter",
                model=self.client.config.model,
                assistant_message=assistant_message,
                error=None,
            )
            self._log_result(result, start)
            return result
        except Exception as exc:
            result = AIConnectivityResponse(
                success=False,
                status="error",
                provider="openrouter",
                model=self.client.config.model,
                assistant_message=None,
                error=f"OpenRouter connectivity request failed: {exc}",
            )
            self._log_result(result, start)
            return result

    def _log_result(self, result: AIConnectivityResponse, start: float) -> None:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ai_connectivity status=%s provider=%s model=%s latency_ms=%s",
            result.status,
            result.provider,
            result.model,
            latency_ms,
        )

    def handle_chat(
        self,
        username: str,
        request: AIChatRequest,
        board_service: BoardService,
    ) -> AIChatResponse:
        start = time.perf_counter()
        current_board = board_service.get_board(username)

        if not self.client.is_configured():
            result = AIChatResponse(
                success=False,
                status="skipped",
                provider="openrouter",
                model=self.client.config.model,
                assistant_message=(
                    "OPENROUTER_API_KEY is not configured. AI chat is unavailable right now."
                ),
                board_updated=False,
                board=current_board,
                error="OPENROUTER_API_KEY is not configured.",
            )
            self._log_chat_result(result, start)
            return result

        try:
            messages = self._build_chat_messages(current_board, request)
            raw_text = self.client.request_messages(
                messages,
                max_tokens=max(self.client.config.max_tokens, MIN_CHAT_MAX_TOKENS),
            )
            assistant_message, board_candidate = self._parse_structured_response(
                raw_text)

            board_updated = False
            board_to_return = current_board
            error: str | None = None

            if board_candidate is not None:
                try:
                    board_payload = BoardPayload.model_validate(
                        board_candidate)
                    board_to_return = board_service.save_board(
                        username, board_payload)
                    board_updated = True
                except Exception as exc:
                    error = f"AI board update ignored: {exc}"

            response_message = assistant_message or FALLBACK_MESSAGE
            status = "success" if assistant_message else "fallback"

            result = AIChatResponse(
                success=True,
                status=status,
                provider="openrouter",
                model=self.client.config.model,
                assistant_message=response_message,
                board_updated=board_updated,
                board=board_to_return,
                error=error,
            )
            self._log_chat_result(result, start)
            return result
        except Exception as exc:
            result = AIChatResponse(
                success=False,
                status="error",
                provider="openrouter",
                model=self.client.config.model,
                assistant_message=FALLBACK_MESSAGE,
                board_updated=False,
                board=current_board,
                error=f"OpenRouter chat request failed: {exc}",
            )
            self._log_chat_result(result, start)
            return result

    def _build_chat_messages(
        self,
        board: dict,
        request: AIChatRequest,
    ) -> list[dict[str, str]]:
        history_payload = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]
        user_payload = {
            "question": request.question,
            "history": history_payload,
            "board": board,
            "response_contract": {
                "userMessage": "string",
                "board": "optional full board object",
            },
        }
        return [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload)},
        ]

    def _parse_structured_response(self, raw_text: str) -> tuple[str | None, dict | None]:
        data = self._try_parse_json(raw_text)
        if data is None:
            recovered_message = self._extract_message_from_raw(raw_text)
            return recovered_message or raw_text.strip(), None

        assistant_message = self._extract_message(data)
        board_candidate = self._extract_board_candidate(data)
        return assistant_message, board_candidate

    def _try_parse_json(self, raw_text: str) -> dict | None:
        stripped = raw_text.strip()
        if not stripped:
            return None

        candidates = [
            stripped,
            self._strip_markdown_fence(stripped),
        ]

        extracted = self._extract_first_balanced_json_object(stripped)
        if extracted:
            candidates.append(extracted)

        fenced_extracted = self._extract_first_balanced_json_object(
            self._strip_markdown_fence(stripped)
        )
        if fenced_extracted:
            candidates.append(fenced_extracted)

        unique_candidates: list[str] = []
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in unique_candidates:
                unique_candidates.append(normalized)

        for candidate in unique_candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _strip_markdown_fence(self, text: str) -> str:
        if not text.startswith("```"):
            return text

        lines = text.splitlines()
        if len(lines) < 3:
            return text

        if lines[-1].strip() != "```":
            return text

        return "\n".join(lines[1:-1]).strip()

    def _extract_first_balanced_json_object(self, text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(text)):
            char = text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char == "{":
                depth += 1
                continue

            if char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]

        return None

    def _extract_message(self, data: dict) -> str | None:
        message_keys = ["userMessage", "assistantMessage", "message", "reply"]
        for key in message_keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_board_candidate(self, data: dict) -> dict | None:
        board_keys = ["board", "boardUpdate", "updatedBoard"]
        for key in board_keys:
            value = data.get(key)
            if isinstance(value, dict):
                return value
        return None

    def _extract_message_from_raw(self, raw_text: str) -> str | None:
        for field_name in ["userMessage", "assistantMessage", "message"]:
            candidate = self._extract_json_string_field(raw_text, field_name)
            if candidate:
                return candidate

        patterns = [
            r'"userMessage"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
            r'"assistantMessage"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
            r'"message"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text)
            if not match:
                continue

            try:
                candidate = bytes(match.group(1), "utf-8").decode(
                    "unicode_escape"
                ).strip()
            except UnicodeDecodeError:
                continue

            if candidate:
                return candidate

        return None

    def _extract_json_string_field(self, raw_text: str, field_name: str) -> str | None:
        key = f'"{field_name}"'
        key_index = raw_text.find(key)
        if key_index == -1:
            return None

        colon_index = raw_text.find(":", key_index + len(key))
        if colon_index == -1:
            return None

        start_index = colon_index + 1
        while start_index < len(raw_text) and raw_text[start_index].isspace():
            start_index += 1

        if start_index >= len(raw_text) or raw_text[start_index] != '"':
            return None

        chars: list[str] = []
        escaped = False
        for index in range(start_index + 1, len(raw_text)):
            char = raw_text[index]
            if escaped:
                chars.append(char)
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                return "".join(chars).strip()
            chars.append(char)

        if chars:
            return "".join(chars).strip()

        return None

    def _log_chat_result(self, result: AIChatResponse, start: float) -> None:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ai_chat status=%s provider=%s model=%s board_updated=%s latency_ms=%s",
            result.status,
            result.provider,
            result.model,
            result.board_updated,
            latency_ms,
        )
