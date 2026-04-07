from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.ai_client import AIConfig, OpenRouterClient
from app.ai_service import AIService
from app.board_service import BoardService
from app.schemas import AIChatRequest, AIChatResponse, AIConnectivityResponse, BoardPayload


def resolve_db_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "pm.db"


def resolve_frontend_dist() -> Path | None:
    candidates = [
        Path(__file__).parent / "static",
        Path(__file__).resolve().parents[2] / "frontend" / "out",
    ]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return None


def create_app(
    static_dir: Path | None = None,
    db_path: Path | None = None,
    ai_service: AIService | None = None,
) -> FastAPI:
    app = FastAPI(title="Project Management MVP Backend")
    service = BoardService(db_path or resolve_db_path())
    service.initialize()
    resolved_ai_service = ai_service or AIService(
        OpenRouterClient(AIConfig.from_env()))

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/hello")
    def hello_api() -> dict[str, str]:
        return {"message": "hello world", "service": "backend"}

    # MVP NOTE: Authentication is frontend-only (hardcoded credentials).
    # The backend accepts any username in the URL with no session validation.
    # This is intentional for the local-only single-user MVP — no user isolation
    # is enforced server-side. Adding server-side auth would require session
    # tokens validated here before delegating to the service layer.
    @app.get("/api/board/{username}")
    def get_board(username: str) -> dict:
        return service.get_board(username)

    @app.put("/api/board/{username}")
    def put_board(username: str, board: BoardPayload) -> dict:
        try:
            return service.save_board(username, board)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/ai/connectivity", response_model=AIConnectivityResponse)
    def ai_connectivity() -> AIConnectivityResponse:
        return resolved_ai_service.check_connectivity()

    @app.post("/api/ai/chat/{username}", response_model=AIChatResponse)
    def ai_chat(username: str, request: AIChatRequest) -> AIChatResponse:
        return resolved_ai_service.handle_chat(username, request, service)

    frontend_dist = static_dir if static_dir is not None else resolve_frontend_dist()
    if frontend_dist and frontend_dist.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(frontend_dist), html=True),
            name="frontend-static",
        )
        return app

    @app.get("/", response_class=HTMLResponse)
    def root() -> str:
        return """
<!doctype html>
<html lang="en">
  <head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PM MVP Backend Smoke Test</title>
  <style>
    body {
    font-family: Arial, sans-serif;
    margin: 2rem;
    line-height: 1.5;
    }
    code {
    background: #f3f3f3;
    padding: 0.15rem 0.35rem;
    border-radius: 0.25rem;
    }
  </style>
  </head>
  <body>
  <h1>Hello from FastAPI</h1>
  <p>This is the Part 2 scaffold static page served at <code>/</code>.</p>
  <p>Smoke API endpoint: <code>/api/hello</code></p>
  </body>
</html>
"""

    return app


app = create_app()
