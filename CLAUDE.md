# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local-only Project Management MVP: a Kanban board with an AI chat sidebar. The FastAPI backend serves the Next.js static build at `/` and exposes all API routes. Everything runs in Docker.

## Commands

### Backend

```bash
cd backend
pip install -e ".[dev]"   # install deps including pytest
pytest tests/             # run all backend tests
pytest tests/test_foo.py  # run a single test file
```

### Frontend

```bash
cd frontend
npm install
npm run dev               # dev server on port 3000
npm run build             # static export to out/
npm run lint              # ESLint
npm run test:unit         # Vitest unit tests (run once)
npm run test:unit:watch   # Vitest in watch mode
npm run test:e2e          # Playwright E2E tests
npm run test:all          # unit + E2E
```

Run a single Vitest test file:
```bash
npx vitest run src/components/KanbanBoard.test.tsx
```

### Docker

```bash
docker compose up    # build and start backend (serves frontend at :8000)
docker compose down  # stop
```

Scripts for start/stop are also in `scripts/` for Mac, Windows, and Linux.

## Architecture

### Request flow

1. Browser hits `http://localhost:8000/` — FastAPI serves the Next.js static build from `frontend/out/` (or `app/static/` in the Docker image).
2. Frontend detects login session state (frontend-only, hardcoded credentials `user`/`password`).
3. On login, frontend calls `GET /api/board/{username}` to load the board, then `PUT /api/board/{username}` to persist changes.
4. AI chat sends `POST /api/ai/chat/{username}` with the current question and full conversation history. The backend fetches the live board, builds the prompt, calls OpenRouter, and applies any AI-suggested board mutations before responding.

### Backend (`backend/`)

- `app/main.py` — `create_app()` factory wires together `BoardService`, `AIService`, all routes, and static file mounting. A module-level `app = create_app()` is the uvicorn entry point.
- `app/board_service.py` — all SQLite reads/writes; owns DB initialization and the board↔API payload transformation.
- `app/ai_client.py` — thin OpenRouter HTTP client; config loaded from env vars (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `OPENROUTER_MAX_TOKENS`, etc.).
- `app/ai_service.py` — orchestrates chat: fetches board, builds prompt, calls client, parses permissive structured JSON response, applies validated board patches via `BoardService`, returns `AIChatResponse`.
- `app/schemas.py` — Pydantic models shared across routes and services.
- Database file: `backend/data/pm.db` (created on first run; not committed).

### Frontend (`frontend/src/`)

- `app/` — Next.js App Router pages.
- `components/KanbanBoard.tsx` — main board component; manages optimistic UI updates, sync status, and triggers backend saves.
- `lib/kanban.ts` — pure board state logic (column/card types and reducers).
- `lib/boardApi.ts` — all `fetch` calls to `/api/board/` and `/api/ai/chat/`; normalizes API payloads to internal `BoardData` type.
- Frontend is built as a static export (`output: 'export'` in `next.config`); no server-side Next.js features.

### AI structured output contract

`AIService.handle_chat` sends the board JSON + conversation history and expects the model to return JSON:
```json
{ "userMessage": "...", "board": { /* optional full board replacement */ } }
```
Parsing is permissive — the service strips markdown fences, extracts the first balanced `{…}` object, and falls back to raw text rather than erroring. Board updates are validated with `BoardPayload.model_validate` before being persisted.

## Coding Standards

- No over-engineering; no unnecessary defensive programming; no extra features beyond what is asked.
- No emojis anywhere.
- Prove root cause before applying fixes — do not guess.
- Target ~80% unit test coverage where sensible; integration tests for cross-boundary paths.
- Optimistic UI updates with explicit sync status/error feedback.
- Color palette: Accent Yellow `#ecad0a`, Blue Primary `#209dd7`, Purple Secondary `#753991`, Dark Navy `#032147`, Gray Text `#888888`.


## DETAILED PLAN

@doc/PLAN.md