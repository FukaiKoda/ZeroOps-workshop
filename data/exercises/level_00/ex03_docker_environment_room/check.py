"""Interactive Docker validation for ex03_docker_environment_room."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

IMAGE_TAG = "grademe-config:v1"
ENV_VAR = "APP_COLOR"
DEFAULT_VALUE = "blue"
OVERRIDE_VALUE = "red"


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


def _normalize_dockerfile(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]


def _has_from_alpine(instructions: list[str]) -> bool:
    for inst in instructions:
        if inst.upper().startswith("FROM "):
            image = inst.split(None, 1)[1].strip()
            return image == "alpine" or image.startswith("alpine:") or image.startswith("alpine@")
    return False


def _extract_env_value(instructions: list[str], var: str) -> Optional[str]:
    for inst in instructions:
        if not inst.upper().startswith("ENV "):
            continue
        rest = inst[4:].strip()
        if "=" in rest:
            key, value = rest.split("=", 1)
            if key.strip().upper() == var.upper():
                return value.strip().strip('"').strip("'")
        else:
            parts = rest.split(None, 1)
            if len(parts) == 2 and parts[0].strip().upper() == var.upper():
                return parts[1].strip().strip('"').strip("'")
    return None


def _cmd_is_correct(instructions: list[str]) -> Tuple[bool, str]:
    cmd_text = " ".join(inst for inst in instructions if inst.upper().startswith("CMD")).lower()
    if not cmd_text:
        return False, "Missing CMD instruction"
    if "$app_color" not in cmd_text:
        return False, "CMD must reference $APP_COLOR"
    if "sleep" not in cmd_text or "infinity" not in cmd_text:
        return False, "CMD must include 'sleep infinity'"
    return True, ""


def _image_exists(tag: str) -> bool:
    code, _, _ = _run_command(["docker", "image", "inspect", tag])
    return code == 0


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


def _image_env(tag: str) -> Tuple[bool, list[str], str]:
    ok, data, err = _inspect_json(["docker", "image", "inspect", tag])
    if not ok or not data:
        return False, [], err
    env = data.get("Config", {}).get("Env", [])
    return (True, [str(e) for e in env], "") if isinstance(env, list) else (False, [], "Could not read image env")


def _containers_from_image(tag: str) -> Tuple[bool, list[Tuple[str, str]], str]:
    code, out, err = _run_command(["docker", "ps", "-a", "--filter", f"ancestor={tag}", "--format", "{{.ID}} {{.Names}}"])
    if code != 0:
        return False, [], err or out or "Failed to list containers"
    containers = []
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            containers.append((parts[0], parts[1]))
    return True, containers, ""


def _container_env(name_or_id: str) -> Tuple[bool, list[str], str]:
    ok, data, err = _inspect_json(["docker", "inspect", name_or_id])
    if not ok or not data:
        return False, [], err
    env = data.get("Config", {}).get("Env", [])
    return (True, [str(e) for e in env], "") if isinstance(env, list) else (False, [], "Could not read container env")


def _container_running(name_or_id: str) -> bool:
    code, out, _ = _run_command(["docker", "ps", "--filter", f"id={name_or_id}", "--format", "{{.ID}}"])
    return code == 0 and bool(out.strip())


def _docker_exec_printenv(name_or_id: str, var: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "exec", name_or_id, "printenv", var], timeout=10)
    return (False, err or out) if code != 0 else (True, out.strip())


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    errors: list[str] = []
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"
    rendu_path = _rendu_dir(exercise_path)
    ok, content, err = _read_text(rendu_path / "Dockerfile")
    if not ok:
        return False, f"Validation failed:\n- Dockerfile not found at {rendu_path / 'Dockerfile'}"
    instructions = _normalize_dockerfile(content)
    if not _has_from_alpine(instructions):
        errors.append("Your image should be based on Alpine")
    env_value = _extract_env_value(instructions, ENV_VAR)
    if env_value != DEFAULT_VALUE:
        errors.append(f"Dockerfile ENV {ENV_VAR} must default to '{DEFAULT_VALUE}'")
    cmd_ok, cmd_error = _cmd_is_correct(instructions)
    if not cmd_ok:
        errors.append(cmd_error)
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    if not _image_exists(IMAGE_TAG):
        return False, f"Image '{IMAGE_TAG}' not found. Build it first."
    ok, image_env, err = _image_env(IMAGE_TAG)
    if not ok or f"{ENV_VAR}={DEFAULT_VALUE}" not in image_env:
        return False, f"Image is missing default ENV {ENV_VAR}={DEFAULT_VALUE}."
    ok, containers, err = _containers_from_image(IMAGE_TAG)
    if not ok or not containers:
        return False, f"Run two containers from '{IMAGE_TAG}', one default and one with -e {ENV_VAR}={OVERRIDE_VALUE}."
    seen_values: set[str] = set()
    red_running_id: Optional[str] = None
    for container_id, _ in containers:
        ok, env, _ = _container_env(container_id)
        if not ok:
            continue
        found = next((e for e in env if e.startswith(f"{ENV_VAR}=")), None)
        if found:
            value = found.split("=", 1)[1]
            seen_values.add(value)
            if value == OVERRIDE_VALUE and _container_running(container_id):
                red_running_id = container_id
    missing = [f"No container evidence found with {ENV_VAR}={value}." for value in (DEFAULT_VALUE, OVERRIDE_VALUE) if value not in seen_values]
    if missing:
        return False, "Validation failed:\n- " + "\n- ".join(missing)
    if red_running_id:
        ok, value = _docker_exec_printenv(red_running_id, ENV_VAR)
        if not ok or value != OVERRIDE_VALUE:
            return False, f"docker exec printenv {ENV_VAR} did not return {OVERRIDE_VALUE}."
    return True, "Nice! Image defaults to blue and the runtime override to red works."
