"""
JWT session tokens and short-lived OAuth state tokens.

- State tokens: correlate a TUI polling client with an in-flight browser OAuth session.
  Stored in memory (PENDING_STATES dict) with a TTL.

- Session tokens: JWT signed with SECRET_KEY, stored by the client locally.
  Identifies the authenticated user on every API request.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from .config import settings

# In-memory state store: {state_token: {status, session_token, created_at}}
# "status" is one of: "pending" | "complete" | "expired"
PENDING_STATES: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# OAuth State Tokens
# ---------------------------------------------------------------------------


def create_state_token() -> str:
    """
    Generate a URL-safe state token used to match the browser callback
    to the polling TUI client.
    """
    state = secrets.token_urlsafe(32)
    PENDING_STATES[state] = {
        "status": "pending",
        "session_token": None,
        "created_at": datetime.now(timezone.utc),
    }
    return state


def complete_state(state: str, session_token: str) -> bool:
    """
    Mark a state token as complete and attach the session token.
    Returns False if the state doesn't exist or has expired.
    """
    entry = PENDING_STATES.get(state)
    if not entry:
        return False

    age = (datetime.now(timezone.utc) - entry["created_at"]).total_seconds()
    if age > settings.AUTH_STATE_TTL_SECONDS:
        PENDING_STATES[state]["status"] = "expired"
        return False

    PENDING_STATES[state]["status"] = "complete"
    PENDING_STATES[state]["session_token"] = session_token
    return True


def poll_state(state: str) -> dict:
    """
    Return the current state of an OAuth flow.
    Cleans up completed/expired entries after they are read.
    Returns: {status: "pending"|"complete"|"expired", token: str|None}
    """
    entry = PENDING_STATES.get(state)
    if not entry:
        return {"status": "expired", "token": None}

    # Check TTL
    age = (datetime.now(timezone.utc) - entry["created_at"]).total_seconds()
    if age > settings.AUTH_STATE_TTL_SECONDS and entry["status"] == "pending":
        PENDING_STATES[state]["status"] = "expired"

    result = {
        "status": entry["status"],
        "token": entry.get("session_token"),
    }

    # Consume completed/expired states so they aren't polled again
    if entry["status"] in ("complete", "expired"):
        PENDING_STATES.pop(state, None)

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
