# Backend Agent Notes

## Purpose

The `backend/` folder contains the FastAPI service for the Project Management MVP.

## Current Part 2 Scope

- FastAPI app scaffold in `app/main.py`
- Smoke endpoints:
- `GET /` serves a hello-world static HTML page
- `GET /api/hello` returns a JSON hello payload
- `GET /healthz` returns service health
- Basic backend smoke tests in `tests/test_smoke.py`
- Container build config via `Dockerfile` using `uv`

## Dependency Management

- Project metadata and dependencies are in `pyproject.toml`.
- The container image installs dependencies via `uv sync --no-dev`.

## Next Responsibilities

- Extend from smoke scaffold to persistent API and database integration.
- Add backend unit/integration tests as features are added.
- Keep endpoints and service logic simple and aligned to MVP requirements.