# Scripts Agent Notes

## Purpose

The `scripts/` folder provides OS-specific wrappers for local Docker Compose lifecycle.

## Current Scripts

- Windows:
- `start-windows.ps1`
- `stop-windows.ps1`
- Linux:
- `start-linux.sh`
- `stop-linux.sh`
- macOS:
- `start-mac.sh`
- `stop-mac.sh`

## Behavior

- Start scripts run `docker compose up --build -d` from the repository root.
- Stop scripts run `docker compose down` from the repository root.

## Usage Notes

- Scripts assume Docker Desktop/Engine and Docker Compose are installed.
- Run scripts from any location; each script resolves repo-root relative to its own path.