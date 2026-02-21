# ZeroOps Server Architecture

The Server is the "Brain" of the ZeroOps platform. It is a FastAPI application that manages user progress, serves exercises, and verifies grading results.

## Key Responsibilities

1. **State Management**: Tracks user levels, XP, and completed exercises in a JSON database (`data/users/*.json`).
2. **Content Delivery**: Serves exercise metadata and grading scripts from `data/exercises/`.
3. **Grading Verification**:
    - Generates a cryptographic `nonce` for every grading request.
    - Validates the grading result submitted by the client against this nonce.
    - Ensures grading is performed within a valid session window.
4. **Rate Limiting**: Protects endpoints using `slowapi` to ensure stability.

## Architecture

- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn (ASGI)
- **Database**: JSON-based flat files (for workshop simplicity and transparency).
- **Configuration**: Loaded via `pydantic-settings` using Environment Variables default definitions.

## Configuration

The server configuration properties can be overridden via `pydantic-settings` environment variables (prepended with `ZEROOPS_`).
By default, the server runs on:

```yaml
HOST: 0.0.0.0
PORT: 8000
DEBUG: false
```

## Directory Structure

```text
server/
├── src/
│   ├── api/            # API Routes (endpoints)
│   ├── core/           # Core logic (Database, Config, Rate Limit)
│   │                   # Note: No custom loaders are used, keeping complexity down.
│   ├── models/         # Pydantic data models representing Exercise & User States
│   └── main.py         # FastAPI App entry point
└── pyproject.toml      # Poetry Dependencies
```

## Running the Server

To run manually for development:
```bash
cd server
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Or using the root Makefile:
```bash
make run-server
```
