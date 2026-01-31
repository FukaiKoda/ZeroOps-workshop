# ZeroOps Exercise Platform

A self-contained client/server exercise platform with:
- **FastAPI** server
- **requests** client with a persistent **TUI**
- **HMAC-signed JSON** for auth
- A **single JSON file** database with file locking and atomic writes

Target runtime: **Python 3.10 or 3.11** (Ubuntu 22.04). Python 3.14 is not supported with the pinned FastAPI/Pydantic versions.

---

## Project Structure
```
.
├── ascii-art.txt
├── client/
│   ├── __init__.py
│   ├── auth.py
│   ├── client.py
│   ├── models.py
│   ├── requirements.txt
│   ├── runner.py
│   └── tui.py
├── server/
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── db.py
│   ├── levels/
│   │   ├── level_1/
│   │   │   ├── starter/solution.py
│   │   │   ├── subject.en.txt
│   │   │   └── testspec.json
│   │   └── level_2/
│   │       ├── starter/solution.py
│   │       ├── subject.en.txt
│   │       └── testspec.json
│   ├── models.py
│   ├── requirements.txt
│   └── test_db.py
└── shared/
    ├── __init__.py
    ├── schema.py
    └── util.py
```

---

## Quick Start
```bash
cd ~/ZeroOps-workshop
python3.11 -m venv .venv   # or python3.10
source .venv/bin/activate
pip install -r server/requirements.txt -r client/requirements.txt
```

### Environment Variables
Set the same secret on both client and server:
```bash
export APP_SECRET="replace-with-a-strong-shared-secret"
export ADMIN_TOKEN="replace-with-admin-token"
export SERVER_URL="http://127.0.0.1:8000"
```

---

## Server
### Run the API
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### DB Tests
```bash
python server/test_db.py
```

---

## Client
### TUI (default)
```bash
python client/client.py
```

The TUI is always running and uses Vim-style command mode:
- Press `:` to enter command mode
- Type a command and press Enter
- Press **Esc** to exit command mode without running anything

**Commands**
- `sync` / `s`
- `subject` / `sub`
- `grademe` / `g`
- `status` / `st`
- `quit` / `q`
- `help` / `h`

### CLI (direct commands)
```bash
python client/client.py sync
python client/client.py subject
python client/client.py grademe
python client/client.py status
```

**Important:** `sync` and `subject` wipe the current level folder before writing `subject.en.txt`.

---

## Workspace Layout
Default base is your **home directory**. The client creates:
```
~/zeroops/
  rendu/
  subjects/
    level01/
    level02/
    ...
```

Only the current level folder is populated with `subject.en.txt`.

---

## Client Workflow (Step-by-Step)
1. **Sync**
   - Client identifies the current user (username/hostname/client_id/timestamp)
   - Server returns the user’s current level
   - Server returns the subject text for the current level
   - Client wipes the current level folder and writes `subject.en.txt`

2. **Work locally**
   - User creates/edits `solution.py` inside the current level folder

3. **Grademe**
   - Client requests the testspec JSON for the current level
   - Client runs local tests using `runner.py`
   - Results are submitted to the server
   - If passed, server increments the level

4. **Status**
   - Shows server level and local metadata

---

## Server Workflow (Step-by-Step)
1. **Sync (`POST /v1/sync`)**
   - Validates HMAC signature
   - Validates timestamp skew
   - Creates user if missing
   - Updates `last_seen`
   - Returns current level + total levels

2. **Subject (`GET /v1/subject`)**
   - Validates HMAC signature
   - Returns subject text for the user’s current level

3. **Testspec (`GET /v1/testspec`)**
   - Validates HMAC signature
   - Returns a JSON testspec (not executable code)

4. **Submit (`POST /v1/submit`)**
   - Validates HMAC signature
   - Stores attempt details in the JSON DB
   - Increments level if tests passed

---

## Authentication
Every request includes:
- `protocol_version`, `username`, `hostname`, `client_id`, `timestamp`

Every request is signed with:
```
X-Signature = hex(hmac_sha256(APP_SECRET, canonical_json_body))
```

Canonical JSON uses sorted keys, no whitespace, UTF‑8.

Timestamp skew is limited to ±5 minutes unless `ALLOW_CLOCK_SKEW=1`.

---

## Database (server/db.py)
- Single JSON file on disk
- File locking via `fcntl.flock`
- Atomic writes via temp file + `os.replace`
- Corruption recovery: backup + clean reset

DB structure:
```json
{
  "users": {
    "alice": {
      "level": 1,
      "created_at": "...",
      "last_seen": "...",
      "client_ids": ["..."],
      "attempts": [
        {
          "level": 1,
          "submitted_at": "...",
          "pass": false,
          "summary": "2/4 tests passed",
          "details": {"...": "..."}
        }
      ]
    }
  }
}
```

---

## Testspec Format
The server only sends JSON, never executable code.
Example:
```json
{
  "level": 1,
  "entrypoint": "solution.py",
  "function": "add",
  "cases": [
    {"name": "simple", "args": [2, 3], "expected": 5}
  ],
  "constraints": {"timeout_seconds": 2}
}
```

The client runner:
- Imports the user’s `solution.py` via `importlib`
- Executes each test case
- Blocks network access (best-effort)
- Enforces per-test timeout with `signal.alarm`
- Captures stdout/stderr
- Returns structured results

---

## Admin Endpoint
```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" "$SERVER_URL/v1/admin/users"
```

Returns list of users and levels.

---

## Example Session
Server:
```bash
export APP_SECRET="dev-secret"
export ADMIN_TOKEN="admin-secret"
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Client:
```bash
export APP_SECRET="dev-secret"
python client/client.py
```

Inside TUI:
```
:sync
:grademe
:status
```

---

## Troubleshooting
**401 Invalid signature**
- Ensure `APP_SECRET` is identical in both client and server shells.

**Python 3.14 errors**
- Use Python 3.10 or 3.11 for this project.

**TUI shows no logo**
- Ensure `ascii-art.txt` exists at repo root.
