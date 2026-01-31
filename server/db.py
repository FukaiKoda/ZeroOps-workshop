from __future__ import annotations

import json
import os
import tempfile
import time
from contextlib import contextmanager
from typing import Any, Dict

import fcntl

from pathlib import Path

from shared.util import now_iso


class JsonDB:
    def __init__(self, path: str) -> None:
        """Initialize the JSON DB file and lock file paths."""
        self.path = path
        self.lock_path = f"{self.path}.lock"
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._atomic_write({"users": {}})
        if not os.path.exists(self.lock_path):
            Path(self.lock_path).touch()

    @contextmanager
    def _locked(self) -> Any:
        """Acquire an exclusive file lock for the duration of the context."""
        with open(self.lock_path, "a+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _read_data(self) -> Dict[str, Any]:
        """Read and parse the JSON DB, recovering from corruption if needed."""
        if not os.path.exists(self.path):
            return {"users": {}}
        with open(self.path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        if not raw.strip():
            return {"users": {}}
        try:
            data = json.loads(raw)
            if not isinstance(data, dict) or "users" not in data:
                return {"users": {}}
            return data
        except json.JSONDecodeError:
            backup = f"{self.path}.bak.{int(time.time())}"
            try:
                os.replace(self.path, backup)
            except OSError:
                pass
            self._atomic_write({"users": {}})
            return {"users": {}}

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """Write JSON data atomically using a temp file + replace."""
        directory = os.path.dirname(self.path)
        fd, tmp_path = tempfile.mkstemp(prefix="db_", suffix=".json", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(data, tmp, indent=2, sort_keys=True)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def load(self) -> Dict[str, Any]:
        """Load and return the full DB content under lock."""
        with self._locked():
            data = self._read_data()
        return data

    def save(self, data: Dict[str, Any]) -> None:
        """Persist the full DB content under lock."""
        with self._locked():
            self._atomic_write(data)

    def get_or_create_user(self, username: str, client_id: str) -> Dict[str, Any]:
        """Get an existing user or create a new user record."""
        with self._locked():
            data = self._read_data()
            users = data.setdefault("users", {})
            now = now_iso()
            if username not in users:
                users[username] = {
                    "level": 1,
                    "created_at": now,
                    "last_seen": now,
                    "client_ids": [client_id],
                    "attempts": [],
                }
            else:
                user = users[username]
                if client_id not in user.get("client_ids", []):
                    user.setdefault("client_ids", []).append(client_id)
            self._atomic_write(data)
            return users[username]

    def update_last_seen(self, username: str, timestamp: str) -> None:
        """Update the user's last_seen timestamp."""
        with self._locked():
            data = self._read_data()
            if username in data.get("users", {}):
                data["users"][username]["last_seen"] = timestamp
                self._atomic_write(data)

    def record_attempt(
        self,
        username: str,
        level: int,
        submitted_at: str,
        passed: bool,
        summary: str,
        details: Dict[str, Any],
    ) -> None:
        """Append an attempt record to the user's history."""
        with self._locked():
            data = self._read_data()
            user = data.setdefault("users", {}).setdefault(
                username,
                {
                    "level": 1,
                    "created_at": submitted_at,
                    "last_seen": submitted_at,
                    "client_ids": [],
                    "attempts": [],
                },
            )
            user.setdefault("attempts", []).append(
                {
                    "level": level,
                    "submitted_at": submitted_at,
                    "pass": passed,
                    "summary": summary,
                    "details": details,
                }
            )
            self._atomic_write(data)

    def increment_level(self, username: str) -> int:
        """Increment and return the user's level."""
        with self._locked():
            data = self._read_data()
            user = data.setdefault("users", {}).setdefault(
                username,
                {
                    "level": 1,
                    "created_at": now_iso(),
                    "last_seen": now_iso(),
                    "client_ids": [],
                    "attempts": [],
                },
            )
            user["level"] = int(user.get("level", 1)) + 1
            self._atomic_write(data)
            return user["level"]
