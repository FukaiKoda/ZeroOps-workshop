"""Interactive Docker validation for ex05_docker_the_vault."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

VOLUME_NAME = "grademe-db-data"
OLD_CONTAINER = "grademe-db"
NEW_CONTAINER = "grademe-db-new"
MOUNT_DEST = "/var/lib/postgresql/data"
DB_NAME = "grademe"
EXPECTED_COUNT = 3

INIT_SQL_CONTENT = """CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100),
    grade INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO submissions (student_name, grade) VALUES
    ('Alice', 95),
    ('Bob', 87),
    ('Charlie', 92);
"""


def _rendu_dir(exercise_path: Path) -> Path:
    return Path.home() / "rendudevops" / exercise_path.name


def _ensure_init_sql(exercise_path: Path) -> None:
    rendu = _rendu_dir(exercise_path)
    rendu.mkdir(parents=True, exist_ok=True)
    init_sql = rendu / "init.sql"
    if not init_sql.exists():
        init_sql.write_text(INIT_SQL_CONTENT)


def setup(exercise_path: Path) -> None:
    _ensure_init_sql(exercise_path)


def _run_command(args: list[str], timeout: int = 10) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except FileNotFoundError:
        return 127, "", f"{args[0]} not found"


def _docker_available() -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=5)
    return (False, err or out or "Docker is not available") if code != 0 else (True, out)


def _volume_exists(name: str) -> bool:
    code, _, _ = _run_command(["docker", "volume", "inspect", name], timeout=10)
    return code == 0


def _container_exists(name: str) -> bool:
    code, out, _ = _run_command(["docker", "ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"], timeout=10)
    return code == 0 and bool(out.strip())


def _container_running(name: str) -> bool:
    code, out, _ = _run_command(["docker", "ps", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"], timeout=10)
    return code == 0 and bool(out.strip())


def _inspect_container(name: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    code, out, err = _run_command(["docker", "inspect", name], timeout=10)
    if code != 0:
        return False, None, err or out or "inspect failed"
    try:
        data = json.loads(out)
        return (True, data[0], "") if isinstance(data, list) and data else (False, None, "Unexpected inspect output")
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse Docker inspect output: {e}"


def _has_named_volume_mount(inspected: Dict[str, Any]) -> bool:
    return any(m.get("Type") == "volume" and m.get("Name") == VOLUME_NAME and m.get("Destination") == MOUNT_DEST for m in inspected.get("Mounts", []))


def _exec_psql_count(container: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "exec", container, "psql", "-U", "postgres", "-d", DB_NAME, "-t", "-A", "-c", "SELECT COUNT(*) FROM submissions;"], timeout=10)
    if code != 0:
        return False, err or out or "psql query failed"
    try:
        count = int(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return False, f"Unexpected COUNT(*) output: {out!r}"
    return (True, "") if count == EXPECTED_COUNT else (False, f"Expected {EXPECTED_COUNT} rows, found {count}.")


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    _ensure_init_sql(exercise_path)
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"
    errors = []
    if not _volume_exists(VOLUME_NAME):
        errors.append(f"Named volume '{VOLUME_NAME}' not found.")
    if _container_exists(OLD_CONTAINER):
        errors.append(f"Container '{OLD_CONTAINER}' still exists.")
    if not _container_exists(NEW_CONTAINER):
        errors.append(f"Container '{NEW_CONTAINER}' not found.")
    elif not _container_running(NEW_CONTAINER):
        errors.append(f"Container '{NEW_CONTAINER}' exists but is not running.")
    else:
        ok, inspected, inspect_error = _inspect_container(NEW_CONTAINER)
        if not ok or not inspected:
            errors.append(inspect_error)
        elif not _has_named_volume_mount(inspected):
            errors.append(f"Container must mount '{VOLUME_NAME}' at '{MOUNT_DEST}'.")
        else:
            ok, query_error = _exec_psql_count(NEW_CONTAINER)
            if not ok:
                errors.append(query_error)
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    return True, "Vault confirmed: the named volume preserved all three rows."
