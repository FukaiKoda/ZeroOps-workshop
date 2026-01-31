from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Attempt:
    """Represents a single submission attempt."""
    level: int
    submitted_at: str
    passed: bool
    summary: str
    details: Dict[str, Any]


@dataclass
class UserRecord:
    """Represents a user record with progress and attempts."""
    level: int
    created_at: str
    last_seen: str
    client_ids: List[str] = field(default_factory=list)
    attempts: List[Attempt] = field(default_factory=list)
