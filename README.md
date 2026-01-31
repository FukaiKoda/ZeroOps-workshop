# ZeroOps Exercise Platform

A minimal client/server exercise platform with:
- **FastAPI** server and **requests** client
- **HMAC-signed JSON** requests
- A **single JSON file** database with file locking
- A **TUI client** that stays up and uses Vim-style `:` commands

This repo is intended for Python **3.10 or 3.11** (Ubuntu 22.04 target).

---

## Contents
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Server](#server)
- [Client (TUI + CLI)](#client-tui--cli)
- [Workspace Layout](#workspace-layout)
- [Exercise Flow](#exercise-flow)
- [Admin Endpoint](#admin-endpoint)
- [Troubleshooting](#troubleshooting)

---

## Quick Start
```bash
cd ~/ZeroOps-workshop
python3.11 -m venv .venv  # or python3.10
source .venv/bin/activate
pip install -r server/requirements.txt -r client/requirements.txt
```

## Environment Variables
Set the same secret on both client and server:
```bash
export APP_SECRET="replace-with-a-strong-shared-secret"
export ADMIN_TOKEN="replace-with-admin-token"
export SERVER_URL="http://127.0.0.1:8000"
```

---

## Server
Run the API server:
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Optional DB tests:
```bash
python server/test_db.py
```

---

## Client (TUI + CLI)

### TUI (default)
Launch the always-on client:
```bash
python client/client.py
```

The TUI works like Vim command mode:
- Press `:` to enter command mode
- Type a command and press **Enter**
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
python client/client.py grademe   # alias for correct
python client/client.py status
```

**Note:** `sync` and `subject` **wipe the current level folder** before writing `subject.en.txt`.

---

## Workspace Layout
Default base: `~`

The client creates this structure:
```
~/zeroops/
  rendu/
  subjects/
    level01/
    level02/
    ...
```

Only the current level folder is populated with a `subject.en.txt` file.

---

## Exercise Flow
1. **Sync** to fetch the subject for your current level.
2. Create or edit your solution file:
   ```bash
   nano ~/zeroops/subjects/level01/solution.py
   ```
3. **Grademe** to run local tests and submit results.
4. If passed, your level increments and the next subject becomes available.

---

## Admin Endpoint
List users and levels:
```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" "$SERVER_URL/v1/admin/users"
```

---

## Example Transcript
```bash
$ cd ~/ZeroOps-workshop
$ python3.11 -m venv .venv
$ source .venv/bin/activate
$ pip install -r server/requirements.txt -r client/requirements.txt
$ export APP_SECRET="dev-secret"
$ export ADMIN_TOKEN="admin-secret"
$ export SERVER_URL="http://127.0.0.1:8000"
$ uvicorn server.app:app --host 0.0.0.0 --port 8000
```

In another terminal:
```bash
$ cd ~/ZeroOps-workshop
$ source .venv/bin/activate
$ export APP_SECRET="dev-secret"
$ python client/client.py
```

Inside the TUI:
```
:sync
:grademe
:status
```

Admin:
```bash
$ curl -H "X-Admin-Token: $ADMIN_TOKEN" "$SERVER_URL/v1/admin/users"
{"users":[{"username":"you","level":1}]}
```

---

## Troubleshooting
**401 Invalid signature**
- Ensure the same `APP_SECRET` is exported in both the server and client shells.

**Python 3.14 errors**
- Use Python 3.10 or 3.11 for this project.
