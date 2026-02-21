# ZeroOps Workshop Platform

![Open Source](https://img.shields.io/badge/Open%20Source-Yes-green)
![License](https://img.shields.io/badge/License-MIT-blue)

A technical workshop platform designed for the "ZeroOps" workshop. This system orchestrates the delivery, grading, and progress tracking of Docker and Kubernetes exercises using a **Thin Client / Thick Server** architecture, with a twist: **Client-Side Grading**.

## 1. System Architecture & Responsibilities

### Client (TUI)
-   **Environment:** Runs centrally on the user's machine (where they have `docker` and `kubectl` access).
-   **Interface:** A rich Terminal User Interface (TUI) built with `Textual`.
-   **Execution Engine:** The client receives grading scripts (`check.py`) from the server and executes them **locally**. This allows the grading logic to inspect the user's actual system state (e.g., running containers, active pods) without requiring a complex remote sandbox.
-   [Read more about the Client Architecture](CLIENT.md)

### Server (The Brain)
-   **State Management:** Tracks user progress, scores, and unlocked levels.
-   **Content Delivery:** Serves exercise metadata, subjects, and grading scripts.
-   **Protection:** Implements Rate Limiting to ensure stability under load.
-   [Read more about the Server Architecture](SERVER.md)

## 2. Key Features

### 🛡️ Rate Limiting
To ensure fair usage and server stability, endpoints are rate-limited using `slowapi`.

### ⚡ Client-Side Grading Flow
1.  **Request**: User clicks "Submit". Client sends `POST /v1/grade`.
2.  **Prepare**: Server generates a `nonce` and retrieves the `check.py` script for the exercise.
3.  **Execute**: Client receives the script and runs it in a subprocess (`LocalGrader`).
    -   **Level 00 (Docker)**: Checks for running containers/images.
    -   **Level 01 (K8s)**: Validates local YAML files AND performs system checks using `kubectl`.
4.  **Verify**: Client sends the result + `nonce` to `POST /v1/verify`.
5.  **Update**: Server validates the `nonce`, updates the user's score/level, and invalidates the nonce.

## 3. Project Structure

```text
.
├── CLIENT.md               # Client documentation
├── SERVER.md               # Server documentation
├── CONTRIBUTING.md         # Contribution guidelines
├── README.md               # This file
├── client/                 # Textual TUI Application
│   ├── src/
│   │   ├── api/            # API Client (ZeroOpsClient)
│   │   ├── tui/            # UI Components (login, dashboard, leaderboard, modals)
│   │   ├── utils/          # Executor (LocalGrader), Config & Signals
│   │   └── main.py         # Entry point
│   └── pyproject.toml
│
├── server/                 # FastAPI Logic
│   ├── src/
│   │   ├── api/            # Routes (endpoints.py)
│   │   ├── core/           # DB, Config, Rate Limit
│   │   ├── models/         # Pydantic data schemas
│   │   └── main.py         # App Entry point
│   └── pyproject.toml
│
├── data/                   # The "Single Source of Truth"
│   ├── exercises/
│   │   ├── level_00/       # Docker Exercises (ex00 - ex09)
│   │   └── level_01/       # Kubernetes Exercises (ex00 - ex11)
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

1.  **Install dependencies**:
    ```bash
    make install
    ```

2.  **Start the Server**:
    Open a terminal and run:
    ```bash
    make run-server
    ```
    The server will start on `http://0.0.0.0:8000`.

3.  **Start the Client**:
    Open a second terminal and run:
    ```bash
    make run-client
    ```
    The client will connect to `http://localhost:8000` by default.

### Testing
-   `make test-health`: Check server connectivity.
-   `make test-grade`: Simulate a grading request.

## 5. Security Note
While the server uses nonces to prevent simple replay attacks, the client-side grading model relies on the user not actively tampering with the local `check.py` execution environment. For a workshop setting, this trade-off allows for a much richer, interactive experience with real infrastructure tools.

## Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.
