"""Interactive Docker validation for ex03_docker_environment_room.

Goal:
Validate understanding of Docker environment variables:
- Setting a default in the Dockerfile with ENV
- Overriding at runtime with `docker run -e`

We validate (in order):
1) Submission workspace + Dockerfile intent (static checks)
2) Image existence: grademe-config:v1
3) Image default env contains APP_COLOR=blue
4) Evidence of running containers created from the image:
   - at least one container with APP_COLOR=blue
   - at least one container with APP_COLOR=red (runtime override)
5) (Best-effort) If a red container is running: `docker exec printenv APP_COLOR` == red
"""

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


def _normalize_dockerfile(content: str) -> list[str]:
    lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def _has_from_alpine(instructions: list[str]) -> bool:
    for inst in instructions:
        if inst.upper().startswith("FROM "):
            image = inst.split(None, 1)[1].strip()
            # Allow tag or digest pinning.
            # Examples: alpine, alpine:3.20, alpine@sha256:...
            return image == "alpine" or image.startswith("alpine:") or image.startswith("alpine@")
    return False


def _extract_env_value(instructions: list[str], var: str) -> Optional[str]:
    var_upper = var.upper()
    for inst in instructions:
        if not inst.upper().startswith("ENV "):
            continue
        rest = inst[4:].strip()
        if not rest:
            continue
        if "=" in rest:
            key, value = rest.split("=", 1)
            if key.strip().upper() == var_upper:
                return value.strip().strip('"').strip("'")
        else:
            parts = rest.split(None, 1)
            if len(parts) == 2 and parts[0].strip().upper() == var_upper:
                return parts[1].strip().strip('"').strip("'")
    return None


def _cmd_is_correct(instructions: list[str]) -> Tuple[bool, str]:
    cmd_lines = [inst for inst in instructions if inst.upper().startswith("CMD")]
    if not cmd_lines:
        return False, "Missing CMD instruction"

    cmd_text = " ".join(cmd_lines)
    lowered = cmd_text.lower()
    # Be flexible about CMD form (shell form vs exec form).
    # We care about outcomes:
    # - The variable is referenced (so it can be overridden at runtime)
    # - The container stays alive (so we can docker exec)
    if "$app_color" not in lowered:
        return False, "CMD must reference $APP_COLOR (not hardcode the color)"
    if "sleep" not in lowered or "infinity" not in lowered:
        return False, "CMD must include 'sleep infinity' so the container stays inspectable"
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
    if not isinstance(env, list):
        return False, [], "Could not read image env"
    return True, [str(e) for e in env], ""


def _containers_from_image(tag: str) -> Tuple[bool, list[Tuple[str, str]], str]:
    code, out, err = _run_command(
        ["docker", "ps", "-a", "--filter", f"ancestor={tag}", "--format", "{{.ID}} {{.Names}}"]
    )
    if code != 0:
        return False, [], err or out or "Failed to list containers"

    containers: list[Tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            containers.append((parts[0], parts[1]))
        elif len(parts) == 1:
            containers.append((parts[0], parts[0]))
    return True, containers, ""


def _container_env(name_or_id: str) -> Tuple[bool, list[str], str]:
    ok, data, err = _inspect_json(["docker", "inspect", name_or_id])
    if not ok or not data:
        return False, [], err
    env = data.get("Config", {}).get("Env", [])
    if not isinstance(env, list):
        return False, [], "Could not read container env"
    return True, [str(e) for e in env], ""


def _container_running(name_or_id: str) -> bool:
    code, out, _ = _run_command(
        ["docker", "ps", "--filter", f"id={name_or_id}", "--format", "{{.ID}}"]
    )
    if code != 0:
        return False
    return bool(out.strip())


def _docker_exec_printenv(name_or_id: str, var: str) -> Tuple[bool, str]:
    code, out, err = _run_command(["docker", "exec", name_or_id, "printenv", var], timeout=10)
    if code != 0:
        return False, err or out
    return True, out.strip()


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    errors: list[str] = []

    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available for interactive validation: {info}"

    rendu_path = _rendu_dir(exercise_path)
    dockerfile_path = rendu_path / "Dockerfile"

    ok, content, err = _read_text(dockerfile_path)
    if not ok:
        errors.append(
            f"Dockerfile not found at {dockerfile_path}"
        )
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    instructions = _normalize_dockerfile(content)

    if not _has_from_alpine(instructions):
        errors.append("your image should be based on alpine (or alpine:<tag>)")

    env_value = _extract_env_value(instructions, ENV_VAR)
    if env_value is None:
        errors.append(f"Dockerfile must define ENV ")
    elif env_value != DEFAULT_VALUE:
        errors.append(f"Dockerfile ENV {ENV_VAR} must default to '{DEFAULT_VALUE}' (got '{env_value}')")

    cmd_ok, cmd_err = _cmd_is_correct(instructions)
    if not cmd_ok:
        errors.append(cmd_err)

    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    if not _image_exists(IMAGE_TAG):
        return False, (
            f"Image '{IMAGE_TAG}' not found. "
        )

    ok, image_env, err = _image_env(IMAGE_TAG)
    if ok:
        expected = f"{ENV_VAR}={DEFAULT_VALUE}"
        if not any(str(e).startswith(f"{ENV_VAR}=") for e in image_env):
            return False, f"Image is missing default ENV {expected}."
        if expected not in image_env:
            # If ENV is present but not the expected value
            found = next((e for e in image_env if str(e).startswith(f"{ENV_VAR}=")), None)
            return False, f"Image default env should be '{expected}', found '{found}'."
    else:
        return False, f"Could not inspect image env: {err}"

    ok, containers, err = _containers_from_image(IMAGE_TAG)
    if not ok:
        return False, err
    if not containers:
        return False, (
            f"No containers found created from '{IMAGE_TAG}'. Run two containers: one default and one with -e {ENV_VAR}={OVERRIDE_VALUE}."
        )

    seen_values: set[str] = set()
    red_running_id: Optional[str] = None

    for container_id, container_name in containers:
        ok, env, _ = _container_env(container_id)
        if not ok:
            continue
        found = next((e for e in env if str(e).startswith(f"{ENV_VAR}=")), None)
        if not found:
            continue
        value = str(found).split("=", 1)[1]
        seen_values.add(value)
        if value == OVERRIDE_VALUE and _container_running(container_id):
            red_running_id = container_id

    missing = []
    if DEFAULT_VALUE not in seen_values:
        missing.append(
            f"No container evidence found with {ENV_VAR}={DEFAULT_VALUE}. Run a default container (no -e override)."
        )
    if OVERRIDE_VALUE not in seen_values:
        missing.append(
            f"No container evidence found with {ENV_VAR}={OVERRIDE_VALUE}. Run a second container."
        )

    if missing:
        return False, "Validation failed:\n- " + "\n- ".join(missing)

    if red_running_id:
        ok, value = _docker_exec_printenv(red_running_id, ENV_VAR)
        if not ok:
            return False, f"Found a running red container but could not exec into it: {value}"
        if value != OVERRIDE_VALUE:
            return False, f"docker exec printenv {ENV_VAR} returned '{value}', expected '{OVERRIDE_VALUE}'."
        return True, "✅ Nice! Image defaults to blue and runtime override to red works (verified with docker exec)."

    return True, (
        "✅ Nice! Image defaults to blue and you have container evidence of the red override. "
        "(Tip: keep a red container running to allow docker exec verification.)"
    )
