# ZeroOps Client

Terminal User Interface (TUI) client for the **ZeroOps Workshop Platform**.
This is a standalone client distribution for students.

## Quick Setup for Students

### 1. Prerequisites
- Python 3.10+
- Poetry (`pip install poetry`)
- Git

### 2. Configuration
Copy `.env.example` to `.env` and set the ZeroOps server URL provided by your instructor:

```bash
cp .env.example .env
```

Edit `.env`:
```env
ZEROOPS_SERVER_URL=http://<school-zeroops-server-ip>:8000
```

### 3. Install Dependencies
```bash
make install
# Or: poetry install
```

### 4. Launch the Client
```bash
make run
# Or: poetry run python src/main.py tui
```

---

## Authentication & Usage Flow

1. **Login with GitHub**: Click "Login with GitHub" in the TUI to open the browser authorization page.
2. **Link Repository**: Link your student exercise repository (`owner/repo`).
3. **Exercises & Submissions**: View exercise subjects, commit your work to your GitHub repository, and click **Submit Exercise** in the TUI. The server automatically validates your exercise files and returns your grade and feedback.

### Workshop Sections

Use the `CI` and `Docker` buttons on the dashboard to switch sections at any time. Progress is tracked independently, so a blocked Docker exercise does not prevent work on CI exercises. Docker checkers run locally against the user's Docker daemon, then send the result and feedback to the server.
