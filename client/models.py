from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Meta:
    """Local metadata stored alongside each level workspace."""
    server_url: str
    username: str
    level: int
    last_sync: str

    @classmethod
    def load(cls, path: Path) -> Optional["Meta"]:
        """Load meta data from disk if it exists."""
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            server_url=data.get("server_url", ""),
            username=data.get("username", ""),
            level=int(data.get("level", 1)),
            last_sync=data.get("last_sync", ""),
        )

    def save(self, path: Path) -> None:
        """Persist meta data to disk."""
        payload = {
            "server_url": self.server_url,
            "username": self.username,
            "level": self.level,
            "last_sync": self.last_sync,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
