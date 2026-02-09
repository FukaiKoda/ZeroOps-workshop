"""Interactive Docker validation for ex07_docker_the_bridge (The Bridge).

This grader validates ONLY what the subject requires and what can be checked
reliably during submission time:

- A custom bridge network exists: grademe-network
- Two containers exist and are running: grademe-db and grademe-api
- Both containers are attached to grademe-network
- grademe-api can resolve and reach grademe-db by name (ping)

We do NOT validate the "default bridge failure" step because it's not a stable,
deterministic artifact.

Contract:
    grade(grader, code, exercise_path) -> (success: bool, message: str)

"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


NETWORK = "grademe-network"
DB_CONTAINER = "grademe-db"
API_CONTAINER = "grademe-api"


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


def _network_exists(name: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "network", "inspect", name], timeout=10)
    if code != 0:
        return False, err or out or "network inspect failed"
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


def _inspect_json(args: list[str]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    code, out, err = _run_command(args, timeout=10)
    if code != 0:
        return False, None, err or out or "inspect failed"
    try:
        data = json.loads(out)
        if isinstance(data, list) and data:
            return True, data[0], ""
        if isinstance(data, dict):
            return True, data, ""
        return False, None, "Unexpected JSON output"
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse JSON: {e}"


def _container_on_network(container: str, network: str) -> Tuple[bool, str]:
    ok, inspected, err = _inspect_json(["docker", "inspect", container])
    if not ok or not inspected:
        return False, err

    networks = inspected.get("NetworkSettings", {}).get("Networks", {})
    if not isinstance(networks, dict):
        return False, "Could not read container networks"

    if network not in networks:
        return False, f"Container '{container}' is not attached to network '{network}'."

    return True, ""


def _ping_from(container: str, host: str) -> Tuple[bool, str]:
    # Alpine usually has ping; if not, that's a student container choice issue.
    code, out, err = _run_command(["docker", "exec", container, "ping", "-c", "3", host], timeout=10)
    if code != 0:
        return False, err or out or "ping failed"

    # Keep it simple: check at least one "bytes from" line.
    if "bytes from" not in out.lower():
        return False, f"Ping did not show expected replies. Output:\n{out}"

    return True, ""


def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    errors: list[str] = []

    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"

    ok, err = _network_exists(NETWORK)
    if not ok:
        errors.append(
            f"Network '{NETWORK}' not found. Create it with: docker network create {NETWORK}"
        )

    for name in (DB_CONTAINER, API_CONTAINER):
        if not _container_exists(name):
            errors.append(f"Container '{name}' not found.")
        elif not _container_running(name):
            errors.append(f"Container '{name}' exists but is not running.")

    if not errors:
        ok, err = _container_on_network(DB_CONTAINER, NETWORK)
        if not ok:
            errors.append(err)
        ok, err = _container_on_network(API_CONTAINER, NETWORK)
        if not ok:
            errors.append(err)

    if not errors:
        ok, err = _ping_from(API_CONTAINER, DB_CONTAINER)
        if not ok:
            errors.append(
                "Name-based connectivity check failed. From 'grademe-api', 'ping grademe-db' must work. "
                f"Details: {err}"
            )

    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    return True, (
        "✅ Bridge built! The custom network exists, both containers are attached, and 'grademe-api' can reach 'grademe-db' by name."
    )
