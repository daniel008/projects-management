from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Project Management MVP Backend")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello_api() -> dict[str, str]:
    return {"message": "hello world", "service": "backend"}


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
