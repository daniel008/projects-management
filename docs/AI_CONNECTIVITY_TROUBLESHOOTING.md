# AI Connectivity Ops Notes (Part 8)

## Environment Variables

- `OPENROUTER_API_KEY`: required for live connectivity calls.
- `OPENROUTER_MODEL`: optional, defaults to `openai/gpt-oss-120b`.
- `OPENROUTER_BASE_URL`: optional, defaults to `https://openrouter.ai/api/v1`.
- `OPENROUTER_TIMEOUT_SECONDS`: optional, defaults to `15`.
- `OPENROUTER_MAX_RETRIES`: optional, defaults to `2`.
- `OPENROUTER_RETRY_BACKOFF_SECONDS`: optional, defaults to `0.3`.
- `OPENROUTER_TEMPERATURE`: optional, defaults to `0`.
- `OPENROUTER_MAX_TOKENS`: optional, defaults to `64`.

## Connectivity Endpoint

- `GET /api/ai/connectivity`
- Returns normalized payload:
  - `success`
  - `status` (`success`, `skipped`, `error`)
  - `provider`
  - `model`
  - `assistantMessage`
  - `error`

## Common Outcomes

- Missing key:
  - `status` is `skipped`.
  - `error` clearly states that `OPENROUTER_API_KEY` is not configured.
- Provider/network failure:
  - `status` is `error`.
  - `error` includes a concise failure message.
- Success:
  - `status` is `success`.
  - `assistantMessage` contains model output for the connectivity prompt.

## Testing and CI

- Backend tests should use mocks/stubs only for OpenRouter behavior.
- Live provider checks are optional and manual, gated by key availability.

## Logging

- Service logs status, provider, model, and latency metadata.
- API keys and request secrets are never logged.
