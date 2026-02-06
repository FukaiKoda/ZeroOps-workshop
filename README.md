# Project Context: 42-style Technical Event Platform

This document outlines the architecture for a technical event platform, similar to the 42 "Moulinette" or "Examshell" but it will be for a "Zeroctl" project that will check the Dockerfile. The system is designed with a focus on integrity, determinism, and a clear separation of concerns between a thin client and a thick server.

## 1. System Architecture & Responsibilities

The system follows a **Thin Client / Thick Server** pattern.

### Client Responsibilities (TUI)
-   **Environment Discovery:** Collect local metadata (username, hostname, current directory).
-   **State Rendering:** Map server-provided JSON to TUI elements (progress bars, text blocks, menus).
-   **Input Handling:** Capture user commands and forward them to the server.
-   **Exercise Setup:** Execute local shell commands (e.g., `git clone` or `mkdir`) based on server instructions.

### Server Responsibilities (The Brain)
-   **Authentication & Session Management:** Identify the user and map them to a session.
-   **The "Engine":** A state machine that determines the next step (e.g., If Exercise 1 is Success, then Exercise 2).
-   **Content Resolution:** Map a user's progress to a specific path in the filesystem or database.
-   **Validation:** Receive "Grade Me" requests and execute grading scripts in a sandbox.

## 2. Communication & State Model

-   **Protocol:** HTTPS + REST/JSON
-   **Statelessness:** The server is stateless, relying on a database for state persistence. This allows for horizontal scalability and resilience.
-   **Request Pattern:** Every client request includes a `session_token` and `client_version`.

### Progression & Validation Flow
1.  **Sync:** Client asks: "Where am I?" Server returns the current state (e.g., `{ "status": "IN_PROGRESS", "exercise_id": "libft_01" }`).
2.  **Action:** User clicks "Submit." Client sends a `POST` to `/v1/grade`.
3.  **Process:** Server triggers a background job (Worker) to pull the user's code, run tests, and update the DB.
4.  **Result:** Client polls `/v1/status` until the grade is ready.

## 3. Data Model

### User Profile (JSON)
Stored in a JSONB column in SQL.
```json
{
  "user_id": "hatim_42",
  "current_level": 3,
  "history": [
    { "ex_id": "00_docker", "status": "success", "score": 100, "timestamp": "..." }
  ],
  "session_context": { "ip": "10.0.0.5", "login_time": "..." }
}
```

### Exercise Metadata
Each exercise directory contains a `meta.json`.
```json
{
  "id": "docker-2",
  "points": 42,
  "requirements": ["docker-1"],
  "setup_script": "setup_docker.sh",
  "test_suite": "tester_v2.py"
}
```

## 4. Exercise Fetching & Storage Mechanism

The server treats exercises as a Content Tree.

### Folder Structure and hierarchy
```
.
├── client/                 # Textual TUI Application
│   ├── src/
│   │   ├── tui/            # UI Components (Screens, Widgets)
│   │   ├── api/            # Client-side API wrappers (httpx)
│   │   ├── utils/          # Config & signal handlers
│   │   └── main.py         # Entry point (Typer CLI)
│   └── pyproject.toml
│
├── server/                 # FastAPI Logic
│   ├── src/
│   │   ├── api/            # Routes (endpoints.py, auth.py)
│   │   ├── core/           # Database & module loader
│   │   ├── models/         # Pydantic schemas (exercise, user)
│   │   └── main.py         # FastAPI Entry point
│   └── pyproject.toml
│
├── data/                   # The "Single Source of Truth"
│   ├── exercises/          # Exercises Content Tree
│   │   └── level_00/
│   │       ├── ex00_k8s_pods/
│   │       │   ├── meta.json
│   │       │   ├── subject.md
│   │       │   ├── check.py    # Grading script
│   │       │   └── solution.yaml
│   │       └── ...             # More exercises
│   └── users/              # JSON "Database" storage (gitignored)
│
└── Makefile                # Shortcuts for (make run-server, make run-client, make dev)
```

### Mechanism
When a user requests their current task, the server looks up `user.current_level` and `user.progress`, then reads the `meta.json` from the corresponding folder. It can generate a signed URL or temporary credentials for the client to download resources.

## 5. Key Design Decisions & Trade-offs

| Feature         | Choice        | Trade-off                                                              |
| --------------- | ------------- | ---------------------------------------------------------------------- |
| Server State    | Stateless     | Requires more DB hits, but allows server restarts without kicking users. |
| Security        | HMAC Signing  | Every client request is signed to prevent spoofing.                    |
| Grading         | Asynchronous  | Using a message queue (Redis/RabbitMQ) prevents the TUI from freezing. |
| Scalability     | Horizontal    | Statelessness allows running multiple instances behind a Load Balancer.  |

## 6. Recommended Technology Stack

-   **Server:** Python (with FastAPI)
-   **Database:** JSON
-   **Client TUI:** Textual (Python)
-   **Sandboxing:** Docker

## 7. Sequence Diagram: Submission Lifecycle

1.  **User:** write `zeroctl test` (to test answers).
2.  **Client:** `POST /v1/submit { "files": ["main.c"], "repo": "git@url..." }`
3.  **Server:** Validates request -> Enqueues Job -> Returns `202 Accepted`.
4.  **Worker:** Spins up Docker -> Clones Code -> Runs `test_suite.py` -> Writes result to a file then compare.
5.  **Client (Polling):** `GET /v1/status`.
6.  **Server:** Returns `{ "status": "finished", "result": "success", "new_level": 4 }`.
7.  **Client:** Renders a celebration animation in the TUI.
