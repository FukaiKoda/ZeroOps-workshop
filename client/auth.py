from __future__ import annotations

import getpass
import hmac
import os
import socket
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from shared.util import canonical_json, now_iso

CLIENT_DIR = Path.home() / ".exercise_platform"
CLIENT_ID_PATH = CLIENT_DIR / "client_id"


def get_client_id() -> str:
    """Return a persistent client UUID stored under ~/.exercise_platform."""
    CLIENT_DIR.mkdir(parents=True, exist_ok=True)
    if CLIENT_ID_PATH.exists():
        return CLIENT_ID_PATH.read_text(encoding="utf-8").strip()
    client_id = str(uuid.uuid4())
    CLIENT_ID_PATH.write_text(client_id, encoding="utf-8")
    return client_id


def build_identity() -> Dict[str, Any]:
    """Build the identity payload attached to every request."""
    return {
        "protocol_version": 1,
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "client_id": get_client_id(),
        "timestamp": now_iso(),
    }


def sign_body(body: Dict[str, Any]) -> str:
    """Compute the hex HMAC signature for a request body."""
    secret = os.getenv("APP_SECRET")
    if not secret:
        raise RuntimeError("APP_SECRET not set")
    return hmac.new(secret.encode("utf-8"), canonical_json(body), "sha256").hexdigest()


def signed_headers(body: Dict[str, Any]) -> Dict[str, str]:
    """Return headers including the HMAC signature for a request body."""
    return {"X-Signature": sign_body(body)}
