"""Interactive Docker validation for ex06_docker_the_vualt (The Vault).

This grader validates ONLY what the subject requires and what can be checked
at submission time in a deterministic way.

Expected submission state (per subject):
- A named volume exists: grademe-db-data
- The original container grademe-db has been removed
- A new container exists and is running: grademe-db-new
- grademe-db-new mounts the named volume to /var/lib/postgresql/data
- Querying the database shows the seeded data still exists (COUNT(*) == 3)

Contract:
    grade(grader, code, exercise_path) -> (success: bool, message: str)

"""

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
    """Return the user's submission directory for this exercise."""
    return Path.home() / "rendudevops" / exercise_path.name


def _ensure_init_sql(exercise_path: Path) -> None:
    """Create init.sql in the user's exercise directory if it doesn't exist."""
    rendu = _rendu_dir(exercise_path)
    rendu.mkdir(parents=True, exist_ok=True)
    init_sql = rendu / "init.sql"
    if not init_sql.exists():
        init_sql.write_text(INIT_SQL_CONTENT)


def setup(exercise_path: Path) -> None:
    """Setup function called when entering the exercise. Creates required files."""
    _ensure_init_sql(exercise_path)


def _run_command(args: list[str], timeout: int = 10) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except FileNotFoundError:
        return 127, "", f"{args[0]} not found"


def _docker_available() -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=5)
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


def _volume_exists(name: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "volume", "inspect", name], timeout=10)
    if code != 0:
        return False, err or out or "volume inspect failed"
    return True, ""


def _container_exists(name: str) -> bool:
    code, out, _ = _run_command(
        ["docker", "ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"],
        timeout=10,
    )
    return code == 0 and bool(out.strip())


def _container_running(name: str) -> bool:
    code, out, _ = _run_command(
        ["docker", "ps", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"],
        timeout=10,
    )
    return code == 0 and bool(out.strip())


def _inspect_container(name: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    code, out, err = _run_command(["docker", "inspect", name], timeout=10)
    if code != 0:
        return False, None, err or out or "inspect failed"
    try:
        data = json.loads(out)
        if isinstance(data, list) and data:
            return True, data[0], ""
        return False, None, "Unexpected inspect output"
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse docker inspect JSON: {e}"


def _has_named_volume_mount(inspected: Dict[str, Any], volume_name: str, dest: str) -> Tuple[bool, str]:
    mounts = inspected.get("Mounts", [])
    if not isinstance(mounts, list):
        return False, "Could not read container mounts"

    for m in mounts:
        if not isinstance(m, dict):
            continue
        if m.get("Type") != "volume":
            continue
        if m.get("Name") != volume_name:
            continue
        if m.get("Destination") != dest:
            continue
        return True, ""

    return (
        False,
        f"Container must mount named volume '{volume_name}' to '{dest}'.",
    )


def _exec_psql_count(container: str) -> Tuple[bool, str]:
    cmd = (
        "SELECT COUNT(*) FROM submissions;"
    )
    code, out, err = _run_command(
        [
            "docker",
            "exec",
            container,
            "psql",
            "-U",
            "postgres",
            "-d",
            DB_NAME,
            "-t",
            "-A",
            "-c",
            cmd,
        ],
        timeout=10,
    )
    if code != 0:
        return False, err or out or "psql query failed"

    value = out.strip()
    if not value:
        return False, "psql returned empty output"

    # psql -t -A should output only a number, but be defensive.
    try:
        count = int(value.splitlines()[-1].strip())
    except ValueError:
        return False, f"Unexpected COUNT(*) output: {value!r}"

    if count != EXPECTED_COUNT:
        return False, f"Expected {EXPECTED_COUNT} rows in submissions, found {count}."

    return True, ""


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    # Ensure init.sql file exists in user's exercise directory
    _ensure_init_sql(exercise_path)
    
    errors: list[str] = []

    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"

    ok, err = _volume_exists(VOLUME_NAME)
    if not ok:
        errors.append(
            f"Named volume '{VOLUME_NAME}' not found. Create it with: docker volume create {VOLUME_NAME}"
        )

    if _container_exists(OLD_CONTAINER):
        errors.append(
            f"Container '{OLD_CONTAINER}' still exists. Remove it to prove resurrection: docker rm -f {OLD_CONTAINER}"
        )

    if not _container_exists(NEW_CONTAINER):
        errors.append(
            f"Container '{NEW_CONTAINER}' not found. Create it from postgres:15-alpine with the volume mounted."
        )
    elif not _container_running(NEW_CONTAINER):
        errors.append(
            f"Container '{NEW_CONTAINER}' exists but is not running. Start it with: docker start {NEW_CONTAINER}"
        )
    else:
        # Container exists and is running - now verify mount and data
        ok, inspected, inspect_err = _inspect_container(NEW_CONTAINER)
        if not ok or not inspected:
            errors.append(f"Could not inspect '{NEW_CONTAINER}': {inspect_err}")
        else:
            ok, mount_err = _has_named_volume_mount(inspected, VOLUME_NAME, MOUNT_DEST)
            if not ok:
                errors.append(mount_err)
            else:
                # Volume mount is correct - now verify data persistence via SQL query
                ok, qerr = _exec_psql_count(NEW_CONTAINER)
                if not ok:
                    errors.append(
                        "Could not verify data persistence via SQL query. "
                        "Make sure the data was properly seeded in the original container "
                        f"and you are using POSTGRES_DB={DB_NAME}. Details: {qerr}"
                    )

    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    return True, (
        "✅ Vault confirmed! The named volume exists, the original container is gone, and the new container "
        "still contains the 3 seeded rows (data persisted across container destruction)."
    )
