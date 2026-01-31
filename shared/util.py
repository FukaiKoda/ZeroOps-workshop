from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict


def canonical_json(data: Dict[str, Any]) -> bytes:
    """Serialize a dict to canonical JSON bytes for HMAC signing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def now_iso() -> str:
    """Return current UTC time as an ISO-8601 string with Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso8601(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and ensure it is timezone-aware (UTC if missing)."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
