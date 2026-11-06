"""Interactive Docker validation for ex04_docker_shared_folder."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

CONTAINER_NAME = "shared_site"
MOUNT_DEST = "/usr/share/nginx/html"
HOST_FOLDER = "site-content"
HOST_INDEX = "index.html"


def _rendu_dir(exercise_path: Path) -> Path:
    return Path.home() / "rendudevops" / exercise_path.name


def _run_command(args: list[str], timeout: int = 30) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except FileNotFoundError:
        return 127, "", f"{args[0]} not found"


def _docker_available() -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10)
    return (False, err or out or "Docker is not available") if code != 0 else (True, out)


def _read_text(path: Path) -> Tuple[bool, str, str]:
    try:
        return True, path.read_text(), ""
    except Exception as e:
        return False, "", str(e)


def _inspect_json(args: list[str]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    code, out, err = _run_command(args)
    if code != 0:
        return False, None, err or out or "inspect failed"
    try:
        data = json.loads(out)
        if isinstance(data, list) and data:
            return True, data[0], ""
        if isinstance(data, dict):
            return True, data, ""
        return False, None, "Unexpected inspect output"
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse Docker inspect output: {e}"


def _container_running(name: str) -> bool:
    code, out, _ = _run_command(["docker", "ps", "--filter", f"name=^{name}$", "--format", "{{.Names}}"])
    return code == 0 and any(line.strip() == name for line in out.splitlines())


def _running_containers() -> Tuple[bool, list[Tuple[str, str]], str]:
    code, out, err = _run_command(["docker", "ps", "--format", "{{.ID}} {{.Names}}"])
    if code != 0:
        return False, [], err or out or "Failed to list running containers"
    containers = []
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            containers.append((parts[0], parts[1]))
    return True, containers, ""


def _docker_exec_cat(name: str, path: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "exec", name, "cat", path], timeout=10)
    return (False, err or out) if code != 0 else (True, out)


def _normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def _parse_docker_time(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"
    rendu_path = _rendu_dir(exercise_path)
    host_index = rendu_path / HOST_FOLDER / HOST_INDEX
    ok, host_content, _ = _read_text(host_index)
    if not ok or not host_content.strip():
        return False, "Validation failed: create a non-empty site-content/index.html first."
    candidates = [(CONTAINER_NAME, CONTAINER_NAME)] if _container_running(CONTAINER_NAME) else _running_containers()[1]
    expected_source = str((rendu_path / HOST_FOLDER).resolve())
    selected = None
    inspected = None
    for container_id, container_name in candidates:
        ok, data, _ = _inspect_json(["docker", "inspect", container_id])
        if not ok or not data or "nginx" not in str(data.get("Config", {}).get("Image", "")).lower():
            continue
        for mount in data.get("Mounts", []):
            if (mount.get("Type") == "bind" and mount.get("Destination") == MOUNT_DEST and (Path(str(mount.get("Source"))).resolve() == Path(expected_source) or str(mount.get("Source", "")).endswith(f"/{HOST_FOLDER}"))):
                selected, inspected = container_name, data
                break
        if selected:
            break
    if not selected or not inspected:
        return False, "Validation failed: no running Nginx container has the required bind mount."
    started_at = _parse_docker_time(str(inspected.get("State", {}).get("StartedAt", "")))
    if not started_at or datetime.fromtimestamp(host_index.stat().st_mtime, tz=timezone.utc) <= started_at:
        return False, "Edit site-content/index.html after starting the container, then submit again."
    ok, container_content = _docker_exec_cat(selected, f"{MOUNT_DEST}/{HOST_INDEX}")
    if not ok or _normalize_text(container_content) != _normalize_text(host_content):
        return False, "The mounted index.html does not match the host file."
    return True, f"Great! The bind mount is live and validated in {selected}."
