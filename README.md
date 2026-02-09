# ZeroOps Workshop Platform

A technical workshop platform designed for the "ZeroOps" workshop. This system orchestrates the delivery, grading, and progress tracking of Docker and Kubernetes exercises using a **Thin Client / Thick Server** architecture, with a twist: **Client-Side Grading**.

## 1. System Architecture & Responsibilities

### Client (TUI)
-   **Environment:** Runs centrally on the user's machine (where they have `docker` and `kubectl` access).
-   **Interface:** A rich Terminal User Interface (TUI) built with `Textual`.
-   **Execution Engine:** The client receives grading scripts (`check.py`) from the server and executes them **locally**. This allows the grading logic to inspect the user's actual system state (e.g., running containers, active pods) without requiring a complex remote sandbox.

### Server (The Brain)
-   **State Management:** Tracks user progress, scores, and unlocked levels.
-   **Content Delivery:** Serves exercise metadata, subjects, and grading scripts.
-   **Verification:** Issues cryptographic nonces to ensure that the grading result submitted by the client corresponds to a valid, recently initiated grading session.
-   **Protection:** Implements Rate Limiting to ensure stability under load (110+ concurrent users).

## 2. Key Features

### 🛡️ Rate Limiting
To ensure fair usage and server stability, endpoints are rate-limited using `slowapi` (IP-based):
-   **Status Checks**: `120/minute` (2 req/sec) - Allows snappy UI updates.
-   **Grading Requests**: `30/minute` (1 req/2 sec) - Prevents spamming the grading engine.
-   **Verification**: `30/minute` - Matches grading frequency.
-   **Leaderboard**: `30/minute`.

### ⚡ Client-Side Grading Flow
1.  **Request**: User clicks "Grade". Client sends `POST /v1/grade`.
2.  **Prepare**: Server generates a `nonce` and retrieves the `check.py` script for the exercise.
3.  **Execute**: Client receives the script and runs it in a subprocess (`LocalGrader`).
    -   **Level 00 (Docker)**: Checks for running containers/images.
    -   **Level 01 (K8s)**: Validates local YAML files AND performs system checks using `kubectl`.
4.  **Verify**: Client sends the result + `nonce` to `POST /v1/verify`.
5.  **Update**: Server validates the `nonce`, updates the user's score/level, and invalidates the nonce.

## 3. Project Structure

```
.
├── client/                 # Textual TUI Application
│   ├── src/
│   │   ├── tui/            # UI Components (Screens, Widgets)
│   │   ├── api/            # API Client & Models
│   │   ├── utils/          # Executor (LocalGrader), Config
│   │   └── main.py         # Entry point
│   └── pyproject.toml
│
├── server/                 # FastAPI Logic
│   ├── src/
│   │   ├── api/            # Routes (endpoints.py)
│   │   ├── core/           # DB, Loader, Rate Limit
│   │   ├── models/         # Pydantic schemas
│   │   └── main.py         # App Entry point
│   └── pyproject.toml
│
├── data/                   # The "Single Source of Truth"
│   ├── exercises/
│   │   └── level_00/       # Docker Exercises (ex00 - ex09)
│   │   └── level_01/       # Kubernetes Exercises (ex00 - ex10)
│   └── users/              # JSON User Database
│
└── Makefile                # Management commands
```

## 4. Getting Started

### Prerequisites
-   Python 3.10+
-   Poetry (`pip install poetry`)
-   Docker & Kubectl (for exercises)

### Quick Start
Run everything in development mode:
```bash
make dev
```
This starts the server in the background and launches the client TUI.

### Testing
-   `make test-status`: Check server connectivity.
-   `make test-grade`: Simulate a grading request.

## 5. Security Note
While the server uses nonces to prevent simple replay attacks, the client-side grading model relies on the user not actively tampering with the local `check.py` execution environment. For a workshop setting, this trade-off allows for a much richer, interactive experience with real infrastructure tools.

