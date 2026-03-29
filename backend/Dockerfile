FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS frontend-builder

WORKDIR /frontend

RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl xz-utils ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz \
	| tar -xJ -C /usr/local --strip-components=1

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY backend/pyproject.toml ./pyproject.toml
COPY backend/app ./app
COPY --from=frontend-builder /frontend/out ./app/static

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
