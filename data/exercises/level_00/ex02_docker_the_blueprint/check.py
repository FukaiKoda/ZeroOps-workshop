"""Interactive Docker validation for ex02_docker_the_blueprint."""

from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import subprocess
import json

DEFAULT_INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>My Custom Page</title>
</head>
<body>
    <h1>Welcome to my custom web artifact!</h1>
    <p>This page was built using Docker.</p>
</body>
</html>
"""


def _rendu_dir(exercise_path: Path) -> Path:
    return Path.home() / "rendudevops" / exercise_path.name


def _ensure_index_html(rendu_path: Path) -> None:
    index_path = rendu_path / "index.html"
    if not index_path.exists():
        try:
            rendu_path.mkdir(parents=True, exist_ok=True)
            index_path.write_text(DEFAULT_INDEX_HTML)
        except Exception:
            pass


def _run_command(args: list[str], timeout: int = 30) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(args, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
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


def _inspect_image(image: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    code, out, err = _run_command(["docker", "image", "inspect", image])
    if code != 0:
        return False, None, err or "Image not found"
    try:
        data = json.loads(out)
        return (True, data[0], "") if data else (False, None, "Empty inspection result")
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse inspection: {e}"


def _get_image_history(image: str) -> Tuple[bool, list, str]:
    code, out, err = _run_command(["docker", "history", image, "--format", "{{.CreatedBy}}", "--no-trunc"])
    if code != 0:
        return False, [], err or "Failed to get image history"
    return True, [line.strip() for line in out.splitlines() if line.strip()], ""


def _validate_dockerfile(dockerfile_path: Path) -> Tuple[bool, list[str]]:
    if not dockerfile_path.exists():
        return False, ["Dockerfile not found"]
    try:
        instructions = [line.strip() for line in dockerfile_path.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        return False, [f"Could not read Dockerfile: {e}"]
    errors = []
    from_lines = [line for line in instructions if line.upper().startswith("FROM")]
    if not from_lines:
        errors.append("Missing FROM instruction")
    elif "nginx:alpine" not in from_lines[0].lower():
        errors.append("FROM instruction should use 'nginx:alpine'")
    copy_lines = [line for line in instructions if line.upper().startswith("COPY")]
    if not copy_lines:
        errors.append("Missing COPY instruction")
    elif "index.html" not in copy_lines[0] or "/usr/share/nginx/html" not in copy_lines[0]:
        errors.append("COPY must copy index.html to /usr/share/nginx/html/")
    expose_lines = [line for line in instructions if line.upper().startswith("EXPOSE")]
    if not expose_lines:
        errors.append("Missing EXPOSE instruction")
    elif "80" not in expose_lines[0]:
        errors.append("EXPOSE must document port 80")
    return not errors, errors


def _validate_index_html(index_path: Path) -> Tuple[bool, list[str]]:
    if not index_path.exists():
        return False, ["index.html not found (it is created automatically)"]
    try:
        return (True, []) if index_path.read_text().strip() else (False, ["index.html is empty"])
    except Exception as e:
        return False, [f"Could not read index.html: {e}"]


def _validate_built_image() -> Tuple[bool, list[str]]:
    image_tag = "web-artifact:v1"
    if not _image_exists(image_tag):
        return False, [f"Image '{image_tag}' not found. Did you build it?"]
    ok, config, err = _inspect_image(image_tag)
    if not ok or not config:
        return False, [f"Could not inspect image: {err}"]
    errors = []
    if "80/tcp" not in config.get("Config", {}).get("ExposedPorts", {}):
        errors.append("Image should expose port 80")
    ok, history, err = _get_image_history(image_tag)
    if ok and not any("COPY" in layer.upper() and "index.html" in layer for layer in history):
        errors.append("Image history does not show a COPY layer for index.html")
    return not errors, errors


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available: {info}"
    rendu_path = _rendu_dir(exercise_path)
    rendu_path.mkdir(parents=True, exist_ok=True)
    _ensure_index_html(rendu_path)
    errors = []
    valid, messages = _validate_dockerfile(rendu_path / "Dockerfile")
    if not valid:
        errors.extend(messages)
    valid, messages = _validate_index_html(rendu_path / "index.html")
    if not valid:
        errors.extend(messages)
    valid, messages = _validate_built_image()
    if not valid:
        errors.extend(messages)
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    return True, "Excellent work! The versioned web artifact is ready for deployment."
