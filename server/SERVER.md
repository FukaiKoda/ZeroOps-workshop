# ZeroOps Server Architecture

The Server is the "Brain" of the ZeroOps platform. It is a FastAPI application that manages user progress, serves exercises, and verifies grading results.

## Key Responsibilities

1.  **State Management**: Tracks user levels, XP, and completed exercises in a JSON database (`data/users/*.json`).
2.  **Content Delivery**: Serves exercise metadata and grading scripts from `data/exercises/`.
3.  **Grading Verification**:
    -   Generates a cryptographic `nonce` for every grading request.
    -   Validates the grading result submitted by the client against this nonce.
    -   Ensures grading is performed within a valid session window.
4.  **Rate Limiting**: Protects endpoints using `slowapi` to ensure stability.

## Architecture

-   **Framework**: FastAPI (Python 3.10+)
-   **Server**: Uvicorn (ASGI)
-   **Database**: JSON-based flat files (for workshop simplicity and transparency).
-   **Configuration**: XDG-compliant, loaded via `pydantic-settings`.

## Configuration

The server configuration is located at `~/.config/zeroops/server.yaml` (or via `ZEROOPS_CONFIG` env var).

```yaml
HOST: 0.0.0.0
PORT: 8000
DEBUG: true
```

## Directory Structure

```
server/
├── src/
│   ├── api/            # API Routes (endpoints, auth)
│   ├── core/           # Core logic (DB, Config, Rate Limit)
│   │   └── config.py   # Settings management
│   ├── models/         # Pydantic data models
│   ├── cli.py          # CLI implementation (zeroctl logic)
│   └── main.py         # App entry point
└── pyproject.toml      # Dependencies
```

## Running the Server

In production, the server is managed by the `zeroops.service` daemon (see [SERVICE.md](./SERVICE.md)).

To run manually for development:
```bash
cd server
poetry run uvicorn src.main:app --reload
```
