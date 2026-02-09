"""Interactive Docker validation for ex05_docker_shared_folder.

Goal:
Validate understanding of bind mounts for development:
- A host folder is mounted into an nginx container
- Changes on the host are visible inside the running container

We validate (in order):
1) Docker availability
2) Submission workspace exists and has site-content/index.html
3) A suitable running nginx container exists (prefer name 'shared_site')
4) The container has a *bind* mount to /usr/share/nginx/html
5) The mounted index.html served path matches the host index.html content
"""

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
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10)
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


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
        return False, None, f"Failed to parse JSON: {e}"


def _container_running(name: str) -> bool:
    code, out, _ = _run_command(["docker", "ps", "--filter", f"name=^{name}$", "--format", "{{.Names}}"])
    if code != 0:
        return False
    return any(line.strip() == name for line in out.splitlines())


def _running_containers() -> Tuple[bool, list[Tuple[str, str]], str]:
    """Return list of (id, name) for running containers."""
    code, out, err = _run_command(["docker", "ps", "--format", "{{.ID}} {{.Names}}"])
    if code != 0:
        return False, [], err or out or "Failed to list running containers"
    containers: list[Tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            containers.append((parts[0], parts[1]))
    return True, containers, ""


def _docker_exec_cat(name: str, path: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "exec", name, "cat", path], timeout=10)
    if code != 0:
        return False, err or out
    return True, out


def _normalize_text(text: str) -> str:
    # Normalize line endings + trailing whitespace for robust comparison
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def _parse_docker_time(value: str) -> Optional[datetime]:
    """Parse Docker's RFC3339-ish timestamps (often ending with 'Z')."""
    if not value:
        return None
    try:
        # Example: 2026-02-07T12:34:56.123456789Z
        cleaned = value.strip()
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+00:00"
        # Python doesn't support nanoseconds; trim fractional seconds if needed.
        if "." in cleaned:
            left, right = cleaned.split(".", 1)
            # right is like: 123456789+00:00
            if "+" in right:
                frac, tz = right.split("+", 1)
                frac = frac[:6]  # microseconds
                cleaned = f"{left}.{frac}+{tz}"
            elif "-" in right:
                frac, tz = right.split("-", 1)
                frac = frac[:6]
                cleaned = f"{left}.{frac}-{tz}"
            else:
                cleaned = f"{left}.{right[:6]}"

        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"

    rendu_path = _rendu_dir(exercise_path)
    host_dir = rendu_path / HOST_FOLDER
    host_index = host_dir / HOST_INDEX

    ok, host_content, err = _read_text(host_index)
    if not ok:
        return False, (
            "Validation failed:\n"
            f"- Missing host file: {host_index}\n"
            "Create it first (any HTML is fine)."
            f" ({err})"
        )

    if not host_content.strip():
        return False, f"Validation failed:\n- {host_index} is empty. Add some HTML content."

    # Prefer a deterministic name if present, but accept any suitable running nginx container.
    candidate_ids: list[Tuple[str, str]] = []
    if _container_running(CONTAINER_NAME):
        candidate_ids.append((CONTAINER_NAME, CONTAINER_NAME))
    else:
        ok, running, err = _running_containers()
        if not ok:
            return False, f"Validation failed:\n- {err}"
        candidate_ids.extend(running)

    ok = False
    inspect: Optional[Dict[str, Any]] = None
    chosen_name_or_id: Optional[str] = None

    expected_source = str(host_dir.resolve())

    def _has_expected_bind_mount(inspect_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        mounts = inspect_data.get("Mounts", [])
        if not isinstance(mounts, list):
            return False, None

        found_summary: Optional[str] = None
        for m in mounts:
            if not isinstance(m, dict):
                continue
            dest = str(m.get("Destination", ""))
            if dest != MOUNT_DEST:
                continue
            m_type = str(m.get("Type", ""))
            source = str(m.get("Source", ""))
            found_summary = f"Type={m_type}, Source={source}, Destination={dest}"

            if m_type != "bind":
                continue

            # Prefer strict: exact source folder.
            try:
                if Path(source).resolve() == Path(expected_source):
                    return True, found_summary
            except Exception:
                pass

            # Allow slightly looser matching (symlinks / normalization).
            if source.endswith(f"/{HOST_FOLDER}"):
                return True, found_summary

        return False, found_summary

    last_mount_summary: Optional[str] = None
    last_image: Optional[str] = None

    for container_id, container_name in candidate_ids:
        ok_i, inspect_i, err_i = _inspect_json(["docker", "inspect", container_id])
        if not ok_i or not inspect_i:
            continue

        image = str(inspect_i.get("Config", {}).get("Image", ""))
        last_image = image
        if "nginx" not in image.lower():
            continue

        mount_ok, summary = _has_expected_bind_mount(inspect_i)
        if summary:
            last_mount_summary = summary
        if not mount_ok:
            continue

        ok = True
        inspect = inspect_i
        chosen_name_or_id = container_name or container_id
        break

    if not ok or not inspect or not chosen_name_or_id:
        details = ""
        if last_image:
            details += f"\n- Last inspected image: {last_image}"
        if last_mount_summary:
            details += f"\n- Last mount seen: {last_mount_summary}"
        return False, (
            "Validation failed:\n"
            "- No running nginx container found with the required bind mount.\n"
            f"Expected a bind mount from '{expected_source}' to '{MOUNT_DEST}'."
            f"{details}\n"
            "Start nginx with a bind mount, for example (recommended deterministic name):\n"
            f"  docker run -d --name {CONTAINER_NAME} -p 8080:80 -v $(pwd)/{HOST_FOLDER}:{MOUNT_DEST} nginx"
        )

    # Enforce the key learning: the file was edited AFTER the container started.
    started_at_raw = str(inspect.get("State", {}).get("StartedAt", ""))
    started_at = _parse_docker_time(started_at_raw)
    if not started_at:
        return False, (
            "Validation failed:\n"
            f"- Could not parse container start time (StartedAt='{started_at_raw}')."
        )

    try:
        host_mtime = datetime.fromtimestamp(host_index.stat().st_mtime, tz=timezone.utc)
    except Exception as e:
        return False, f"Validation failed:\n- Could not read mtime for {host_index}: {e}"

    if host_mtime <= started_at:
        return False, (
            "Validation failed:\n"
            "- Your host index.html does not appear to have been edited AFTER the container started.\n"
            "This lab requires proving live updates via a bind mount.\n"
            "Fix:\n"
            "  1) Start the container with the bind mount\n"
            "  2) Edit and save site-content/index.html\n"
            "  3) Submit again"
        )

    ok, container_content = _docker_exec_cat(chosen_name_or_id, f"{MOUNT_DEST}/{HOST_INDEX}")
    if not ok:
        return False, (
            "Validation failed:\n"
            f"- Could not read {MOUNT_DEST}/{HOST_INDEX} inside the container: {container_content}"
        )

    if _normalize_text(container_content) != _normalize_text(host_content):
        return False, (
            "Validation failed:\n"
            "- The container's /usr/share/nginx/html/index.html does not match your host site-content/index.html.\n"
            "This usually means the folder is not mounted correctly (or you mounted the wrong path)."
        )

    return True, f"✅ Great! Your bind mount is correct and you edited the file after start (container: {chosen_name_or_id})."
