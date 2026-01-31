from __future__ import annotations

import hmac
import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import Header, HTTPException, Request, status

from shared.util import canonical_json, parse_iso8601


def _get_secret() -> bytes:
    """Load the shared secret used for HMAC validation."""
    secret = os.getenv("APP_SECRET")
    if not secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="APP_SECRET not set")
    return secret.encode("utf-8")


def _extract_identity(body: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the identity sub-object from a request body."""
    if "identity" in body and isinstance(body["identity"], dict):
        return body["identity"]
    return body


def _verify_timestamp(identity: Dict[str, Any]) -> None:
    """Enforce timestamp skew limits unless explicitly disabled by env."""
    allow_skew = os.getenv("ALLOW_CLOCK_SKEW", "0") == "1"
    if allow_skew:
        return
    max_skew = int(os.getenv("MAX_SKEW_SECONDS", "300"))
    ts_raw = identity.get("timestamp")
    if not ts_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing timestamp")
    try:
        ts = parse_iso8601(ts_raw)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp")
    now = datetime.now(timezone.utc)
    if abs((now - ts).total_seconds()) > max_skew:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Timestamp skew too large")


async def verify_request_signature(request: Request, x_signature: str = Header(default="")) -> Dict[str, Any]:
    """Verify request HMAC signature and timestamp; return parsed JSON body."""
    body_bytes = await request.body()
    if not body_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing JSON body")
    try:
        body_json = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

    expected = hmac.new(_get_secret(), canonical_json(body_json), "sha256").hexdigest()
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    identity = _extract_identity(body_json)
    _verify_timestamp(identity)

    return body_json
