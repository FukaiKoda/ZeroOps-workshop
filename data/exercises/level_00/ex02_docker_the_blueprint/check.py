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
    """Get the user's submission directory."""
    return Path.home() / "rendudevops" / exercise_path.name


def _ensure_index_html(rendu_path: Path) -> None:
    """Auto-create index.html if it doesn't exist."""
    index_path = rendu_path / "index.html"
    if not index_path.exists():
        try:
            rendu_path.mkdir(parents=True, exist_ok=True)
            index_path.write_text(DEFAULT_INDEX_HTML)
        except Exception:
            pass


def _run_command(args: list[str], timeout: int = 30) -> Tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
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
        return 127, "", "docker not found"


def _docker_available() -> Tuple[bool, str]:
    """Check if Docker daemon is available."""
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"])
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


def _image_exists(image: str) -> bool:
    """Check if a Docker image exists locally."""
    code, _, _ = _run_command(["docker", "image", "inspect", image])
    return code == 0


def _inspect_image(image: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Inspect a Docker image and return its configuration."""
    code, out, err = _run_command(["docker", "image", "inspect", image])
    if code != 0:
        return False, None, err or "Image not found"
    try:
        data = json.loads(out)
        if data and len(data) > 0:
            return True, data[0], ""
        return False, None, "Empty inspection result"
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse image inspection: {e}"


def _get_image_history(image: str) -> Tuple[bool, list, str]:
    """Get the layer history of a Docker image."""
    code, out, err = _run_command(
        ["docker", "history", image, "--format", "{{.CreatedBy}}", "--no-trunc"]
    )
    if code != 0:
        return False, [], err or "Failed to get image history"
    layers = [line.strip() for line in out.splitlines() if line.strip()]
    return True, layers, ""


def _validate_dockerfile(dockerfile_path: Path) -> Tuple[bool, list[str]]:
    """Validate the Dockerfile content and return list of errors."""
    errors = []

    if not dockerfile_path.exists():
        return False, ["Dockerfile not found"]

    try:
        content = dockerfile_path.read_text()
    except Exception as e:
        return False, [f"Could not read Dockerfile: {e}"]

    lines = content.strip().splitlines()

    instructions = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            instructions.append(stripped)

    if not instructions:
        return False, ["Dockerfile is empty"]

    from_found = False
    for inst in instructions:
        if inst.upper().startswith("FROM"):
            from_found = True
            if "nginx:alpine" not in inst.lower():
                errors.append(
                    "FROM instruction should use 'nginx:alpine' as the base image"
                )
            break

    if not from_found:
        errors.append("Missing FROM instruction")

    copy_found = False
    copy_correct = False
    for inst in instructions:
        if inst.upper().startswith("COPY"):
            copy_found = True
            if "index.html" in inst and "/usr/share/nginx/html" in inst:
                copy_correct = True
            break

    if not copy_found:
        errors.append("Missing COPY instruction")
    elif not copy_correct:
        errors.append(
            "COPY instruction should copy index.html to /usr/share/nginx/html/"
        )

    expose_found = False
    expose_80 = False
    for inst in instructions:
        if inst.upper().startswith("EXPOSE"):
            expose_found = True
            if "80" in inst:
                expose_80 = True
            break

    if not expose_found:
        errors.append("Missing EXPOSE instruction")
    elif not expose_80:
        errors.append("EXPOSE instruction should document port 80")

    for inst in instructions:
        if inst.upper().startswith("CMD"):
            break

    return len(errors) == 0, errors


def _validate_index_html(index_path: Path) -> Tuple[bool, list[str]]:
    """Validate that index.html exists and has content."""
    errors = []

    if not index_path.exists():
        return False, ["index.html not found (should have been auto-created)"]

    try:
        content = index_path.read_text()
        if not content.strip():
            errors.append("index.html is empty")
    except Exception as e:
        return False, [f"Could not read index.html: {e}"]

    return len(errors) == 0, errors


def _validate_built_image() -> Tuple[bool, list[str]]:
    """Validate that web-artifact:v1 image is built correctly."""
    errors = []
    image_tag = "web-artifact:v1"

    if not _image_exists(image_tag):
        return False, [f"Image '{image_tag}' not found. Did you build it"]

    ok, config, err = _inspect_image(image_tag)
    if not ok:
        errors.append(f"Could not inspect image: {err}")
        return False, errors

    exposed_ports = config.get("Config", {}).get("ExposedPorts", {})
    if "80/tcp" not in exposed_ports:
        errors.append("Image should have port 80 exposed (EXPOSE 80)")

    ok, history, err = _get_image_history(image_tag)
    if ok:
        copy_layer_found = False
        for layer in history:
            if "COPY" in layer.upper() and "index.html" in layer:
                copy_layer_found = True
                break
        if not copy_layer_found:
            errors.append("Image history doesn't show a COPY layer for index.html")

    return len(errors) == 0, errors


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grade ex03_docker_the_blueprint.

    Validates:
    1. Dockerfile exists with correct instructions
    2. index.html exists
    3. Image web-artifact:v1 is built
    4. Image has correct configuration
    """
    all_errors = []
    warnings = []

    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available: {info}"

    rendu_path = _rendu_dir(exercise_path)

    if not rendu_path.exists():
        try:
            rendu_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            all_errors.append(f"Could not create submission directory: {e}")
            return False, "Validation failed:\n- " + "\n- ".join(all_errors)

    _ensure_index_html(rendu_path)

    dockerfile_path = rendu_path / "Dockerfile"
    index_path = rendu_path / "index.html"

    df_ok, df_errors = _validate_dockerfile(dockerfile_path)
    if not df_ok:
        all_errors.extend(df_errors)

    idx_ok, idx_errors = _validate_index_html(index_path)
    if not idx_ok:
        all_errors.extend(idx_errors)

    img_ok, img_errors = _validate_built_image()
    if not img_ok:
        all_errors.extend(img_errors)

    if all_errors:
        error_msg = "Validation failed:\n- " + "\n- ".join(all_errors)
        if warnings:
            error_msg += "\n\nWarnings:\n- " + "\n- ".join(warnings)
        return False, error_msg

    success_msg = """✅ Excellent work! Your Dockerfile is correct!

You've successfully:
• Created a Dockerfile with nginx:alpine base
• Copied index.html to the correct nginx directory
• Documented port 80 with EXPOSE
• Built the image as web-artifact:v1

Your custom web artifact is ready for deployment! 🚀"""

    return True, success_msg
