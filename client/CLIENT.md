# ZeroOps Client Architecture

The Client is a **Terminal User Interface (TUI)** built with `Textual`. It runs locally on the user's machine and interacts with the ZeroOps Server.

## Key Responsibilities

1.  **User Interface**: Provides a rich, interactive dashboard for viewing exercises, status, and leaderboards.
2.  **Authentication**: Handles OAuth-like authentication flow (via browser).
3.  **Local Execution**:
    -   Receives grading scripts (`check.py`) from the server.
    -   Executes them **locally** in a subprocess.
    -   This allows the script to inspect the user's *actual* Docker/Kubernetes environment (`docker ps`, `kubectl get pods`).
4.  **Submission**: Sends the execution result + nonce back to the server.

## Architecture

-   **Framework**: Textual (Python TUI)
-   **HTTP Client**: `httpx` (Async)
-   **Executor**: `src.utils.executor.LocalGrader` (Runs python scripts safely).

## How "Client-Side Grading" Works

1.  **Request**: User clicks "Submit". Client asks Server for the grading script.
2.  **Receive**: Server returns the script content + a unique `nonce`.
3.  **Execute**: Client writes the script to a temp file and runs it:
    ```bash
    python temp_runner.py
    ```
    The script checks for running containers/pods on the host machine.
4.  **Verify**: Client sends `{nonce, success, logs}` back to the server.

## Configuration

The client auto-discovers environment settings but defaults to:
-   **Server URL**: `http://127.0.0.1:8000`
-   **Workspace**: `~/rendudevops` (Where exercises are solved).

## Directory Structure

```
client/
├── src/
│   ├── tui/            # UI Screens (Dashboard, Login, Leaderboard)
│   ├── api/            # API Client (ZeroOpsClient)
│   ├── utils/          # Executor, Config
│   └── main.py         # Entry point (tui command)
└── pyproject.toml      # Dependencies
```

## Running the Client

The client is best launched via the `zeroctl` tool:
```bash
zeroctl ui
```
