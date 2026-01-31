from __future__ import annotations

import os
import tempfile
import threading
from typing import List

try:
    from server.db import JsonDB
except ImportError:  # pragma: no cover
    from db import JsonDB


def test_read_write() -> None:
    """Verify basic load/save and user creation."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "db.json")
        db = JsonDB(path)
        data = db.load()
        assert "users" in data
        db.get_or_create_user("alice", "cid")
        data2 = db.load()
        assert "alice" in data2["users"]


def test_concurrent_writes() -> None:
    """Verify that concurrent writes do not corrupt the DB."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "db.json")
        db = JsonDB(path)
        db.get_or_create_user("alice", "cid")

        errors: List[Exception] = []

        def worker(i: int) -> None:
            try:
                db.record_attempt("alice", 1, f"t{i}", False, "0/1", {"i": i})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        data = db.load()
        attempts = data["users"]["alice"].get("attempts", [])
        assert len(attempts) == 10


if __name__ == "__main__":
    test_read_write()
    test_concurrent_writes()
    print("db tests passed")
