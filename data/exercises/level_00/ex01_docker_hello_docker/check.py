"""Interactive Docker validation for this exercise."""

from pathlib import Path
from typing import Optional, Tuple
import subprocess


def _run_command(args: list[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "docker not found"


def _docker_available() -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"])
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


def _image_exists(image: str) -> bool:
    code, _, _ = _run_command(["docker", "image", "inspect", image])
    return code == 0


def _hello_world_container_id() -> Optional[str]:
    code, out, _ = _run_command(
        ["docker", "ps", "-a", "--filter", "ancestor=hello-world", "--format", "{{.ID}}"]
    )
    if code != 0:
        return None
    for line in out.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return None


def _container_logs(container_id: str) -> Optional[str]:
    code, out, err = _run_command(["docker", "logs", container_id])
    if code != 0:
        return None if not err else f"{out}\n{err}".strip()
    return out


def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    errors = []

    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"

    if not (_image_exists("hello-world:latest") or _image_exists("hello-world")):
        errors.append("hello-world image not found locally. Pull and run it first.")

    container_id = _hello_world_container_id()
    if not container_id:
        errors.append("No container found from the hello-world image.")
    else:
        logs = _container_logs(container_id)
        if not logs:
            errors.append("Could not read logs from the hello-world container.")
        elif "Hello from Docker!" not in logs:
            errors.append("Expected output not found in container logs. Make sure you run hello-world.")

    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    return True, "✅ Great! Docker is working and the hello-world image ran successfully."
