"""
JWT session tokens and persistent OAuth state tokens.

- State tokens: correlate a TUI polling client with an in-flight browser OAuth session.
  Persisted to DATA_DIR/pending_states.json so uvicorn reloads never drop in-flight logins.

- Session tokens: JWT signed with SECRET_KEY, stored by the client locally.
  Identifies the authenticated user on every API request.
"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from .config import settings

STATE_FILE = settings.DATA_DIR / "pending_states.json"


def _load_states() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_states(states: dict) -> None:
    try:
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(states, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# OAuth State Tokens
# ---------------------------------------------------------------------------


def create_state_token() -> str:
    """
    Generate a URL-safe state token used to match the browser callback
    to the polling TUI client. Persisted to disk for process resilience.
    """
    state = secrets.token_urlsafe(32)
    states = _load_states()
    states[state] = {
        "status": "pending",
        "session_token": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_states(states)
    return state


def complete_state(state: str, session_token: str) -> bool:
    """
    Mark a state token as complete and attach the session token.
    Returns False if the state doesn't exist or has expired.
    """
    states = _load_states()
    entry = states.get(state)
    if not entry:
        return False

    try:
        created_at = datetime.fromisoformat(entry["created_at"])
    except Exception:
        created_at = datetime.now(timezone.utc)

    age = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age > settings.AUTH_STATE_TTL_SECONDS:
        states[state]["status"] = "expired"
        _save_states(states)
        return False

    states[state]["status"] = "complete"
    states[state]["session_token"] = session_token
    _save_states(states)
    return True


def poll_state(state: str) -> dict:
    """
    Return the current state of an OAuth flow.
    Cleans up completed/expired entries after they are read.
    Returns: {status: "pending"|"complete"|"expired", token: str|None}
    """
    states = _load_states()
    entry = states.get(state)
    if not entry:
        return {"status": "expired", "token": None}

    try:
        created_at = datetime.fromisoformat(entry["created_at"])
    except Exception:
        created_at = datetime.now(timezone.utc)

    age = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age > settings.AUTH_STATE_TTL_SECONDS and entry["status"] == "pending":
        entry["status"] = "expired"

    result = {
        "status": entry["status"],
        "token": entry.get("session_token"),
    }

    # Consume completed/expired states so they aren't polled again
    if entry["status"] in ("complete", "expired"):
        states.pop(state, None)
        _save_states(states)

    return result


# ---------------------------------------------------------------------------
# JWT Session Tokens
# ---------------------------------------------------------------------------


def create_session_token(user_id: int) -> str:
    """
    Create a JWT session token for a successfully authenticated user.
    The client stores this locally and sends it as `Authorization: Bearer <token>`.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_session_token(token: str) -> Optional[int]:
    """
    Decode and validate a JWT session token.
    Returns the user_id (int) on success, None on failure.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        return int(user_id_str)
    except (JWTError, ValueError):
        return None
