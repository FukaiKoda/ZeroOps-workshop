# Contributing to ZeroOps

Thank you for your interest in contributing to ZeroOps! We welcome contributions from everyone.

## Repository Overview

- This repository is split into two independent parts: `client/` and `server/`.
- The `client/` side is a `Textual`-based TUI that performs local grading mechanisms.
- The `server/` side is a `FastAPI` application that powers state orchestration.
- The `data/` folder houses all the exercises and users json configurations.

Please refer to [CLIENT.md](CLIENT.md) and [SERVER.md](SERVER.md) for more info.

## How to Contribute

1.  **Fork the repository** on GitHub.
2.  **Clone the project** to your local machine.
3.  **Create a new branch** for your feature or bug fix.
4.  **Make your changes** and commit them with clear messages.
5.  **Push your changes** to your fork.
6.  **Submit a Pull Request** to the main repository.

## Development Setup

### Prerequisites

-   Python 3.10+
-   Poetry (`pip install poetry`)
-   Docker & Kubectl (for exercises)

### Running Locally

1.  **Install Dependencies**:
    ```bash
    make install
    ```

2.  **Start the Server**:
    Open a terminal and run:
    ```bash
    make run-server
    ```

3.  **Start the Client**:
    Open a second terminal and run:
    ```bash
    make run-client
    ```

## Adding New Exercises

We highly encourage contributions that add `level_XX` exercises for tools *other* than Docker and Kubernetes (which are already extensively covered). However, there is always room for improvement, so submitting new exercises or refining existing ones for these technologies is also welcome!

### Exercise Structure

Each exercise lives in `data/exercises/level_XX/exYY_name/` and must contain exactly three files:

1. **`meta.json`**:
   Contains exercise metadata, pointing out the score and type.
   ```json
   {
     "id": "exYY_name",
     "title": "Exercise Title",
     "points": 10,
     "requirements": [],
     "type": "docker" // e.g., 'docker', 'kubernetes', 'terraform', 'interactive', 'python'
   }
   ```

2. **`subject.md`**:
   The markdown file rendered on the client TUI. It should contain the scenario, objective, provided resources, task list, constraints, and hints.

3. **`check.py`**:
   The grading script executed by the client to validate the user's local system. It must strictly implement a `grade(code: str, exercise_path: Path) -> Tuple[bool, str]` function that returns `(True, "Success message")` on success or `(False, "Error message")` on failure.

## Code Style

-   We strictly use `black` and `ruff` for code formatting and linting.
-   Ensure no unused dependencies and variables persist in your PRs.
-   Keep modules cleanly isolated (TUI components in UI files, API logic in bindings).

## Reporting Issues

If you find a bug or have a suggestion, please open an issue on the GitHub repository.
