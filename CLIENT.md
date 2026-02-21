# ZeroOps Client Architecture

The Client is a **Terminal User Interface (TUI)** built with `Textual`. It runs locally on the user's machine and interacts with the ZeroOps Server.

## Key Responsibilities

1. **User Interface**: Provides a rich, interactive dashboard for viewing exercises, status, and leaderboards.
2. **Local Execution**:
    - Receives grading scripts (`check.py`) from the server.
    - Executes them **locally** in a subprocess.
    - This allows the script to inspect the user's *actual* Docker/Kubernetes environment (`docker ps`, `kubectl get pods`).
3. **Submission**: Sends the execution result + nonce back to the server.

## Architecture

- **Framework**: Textual (Python TUI)
- **HTTP Client**: `httpx` (Async)
- **Executor**: `src.utils.executor.LocalGrader` (Runs Python grading scripts safely).

## How "Client-Side Grading" Works

1. **Request**: User clicks "Submit". Client asks the Server for the grading script.
2. **Receive**: Server returns the script content + a unique `nonce`.
3. **Execute**: Client writes the script to a temp file and runs it:
    ```bash
    python temp_runner.py
    ```
    The script checks for running containers/pods on the host machine.
4. **Verify**: Client sends `{nonce, success, logs}` back to the server.

## Configuration

The client auto-discovers environment settings but defaults to:
- **Server URL**: `http://localhost:8000`
- **Workspace**: `~/rendudevops` (Where users solve their exercises).

## Directory Structure

```text
client/
├── src/
│   ├── api/            # API Client bindings (ZeroOpsClient)
│   ├── tui/            # UI System
│   │   ├── dashboard.py    # Main user exercise view
│   │   ├── leaderboard.py  # Global ranking system
│   │   ├── login.py        # Entry screen
│   │   ├── modals.py       # Modal popups
│   │   └── screens.py      # Entrypoint module export
│   ├── utils/          # Subprocess Executor, Config handling, OS Signals
│   └── main.py         # Entry point (tui command)
└── pyproject.toml      # Poetry Dependencies
```

## Running the Client

The client is launched using Poetry:
```bash
cd client
poetry run python src/main.py tui
```
Or using the root Makefile:
```bash
make run-client
```
