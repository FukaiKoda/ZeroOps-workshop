"""Interactive Docker validation for Lab 01: Coming Soon.

Goal:
Validate the full container lifecycle with nginx:alpine:
1. Pull and run container with proper naming and port mapping
2. Demonstrate diagnostic skills (logs, stats, exec)
3. Complete lifecycle management (stop/start/remove)

Final expected state:
- nginx:alpine image exists locally
- proof.txt exists with diagnostic evidence
- Container 'coming-soon' has been removed (no ghosts)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

REQUIRED_IMAGE = "nginx:alpine"
CONTAINER_NAME = "coming-soon"
HOST_PORT = 8080
CONTAINER_PORT = 80


def _rendu_dir(exercise_path: Path) -> Path:
    """Get the user's submission directory."""
    return Path.home() / "rendudevops" / exercise_path.name


def _run_command(args: list[str], timeout: int = 30) -> Tuple[int, str, str]:
    """Execute a command and return exit code, stdout, stderr."""
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
    """Check if Docker daemon is running."""
    code, out, err = _run_command(
        ["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10
    )
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


def _image_exists(image: str) -> bool:
    """Check if a Docker image exists locally."""
    code, _, _ = _run_command(["docker", "image", "inspect", image])
    return code == 0


def _container_exists(name: str) -> bool:
    """Check if a container with given name exists (running or stopped)."""
    code, _, _ = _run_command(["docker", "container", "inspect", name])
    return code == 0


def _container_running(name: str) -> bool:
    """Check if a container is currently running."""
    code, out, _ = _run_command(
        ["docker", "inspect", "--format", "{{.State.Running}}", name]
    )
    return code == 0 and out.lower() == "true"


def _get_container_image(name: str) -> Optional[str]:
    """Get the exact image name used by a container."""
    code, out, _ = _run_command(
        ["docker", "inspect", "--format", "{{.Config.Image}}", name]
    )
    if code != 0:
        return None
    return out


def _container_port(name: str, container_port: str = "80") -> Optional[str]:
    """Get host port mapped to container port."""
    code, out, _ = _run_command(
        [
            "docker",
            "inspect",
            "--format",
            f'{{{{(index (index .NetworkSettings.Ports "{container_port}/tcp") 0).HostPort}}}}',
            name,
        ]
    )
    if code != 0 or not out or out == "<no value>":
        return None
    return out


def _check_port_with_curl(port: int) -> bool:
    """Check if a port is accessible using curl (more reliable than raw socket)."""
    code, _, _ = _run_command(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            f"http://localhost:{port}",
        ],
        timeout=5,
    )
    return code == 0


def _validate_proof_file(rendu_path: Path) -> Tuple[bool, List[str], List[str]]:
    successes = []
    errors = []
    proof_file = rendu_path / "proof.txt"

    if not proof_file.exists():
        errors.extend([
            "proof.txt not found in submission directory.",
            f"  -> Create it at: {proof_file}",
            "  -> Save output of logs, stats, and nginx version commands.",
        ])
        return False, successes, errors

    try:
        content = proof_file.read_text().lower()
    except Exception as e:
        errors.append(f"Could not read proof.txt: {e}")
        return False, successes, errors

    if not content.strip():
        errors.append("proof.txt is empty")
        return False, successes, errors

    checks = [
        (any(re.search(p, content) for p in [r"nginx", r"\d{4}/\d{2}/\d{2}", r"start\s*(worker|master)", r"listening"]), "Logs output found in proof.txt", "No logs evidence found in proof.txt"),
        (any(re.search(p, content) for p in [r"cpu\s*%", r"mem\s*(usage|%)", r"container\s+id", r"net\s+i/o", r"\d+\.\d+%", r"\d+(\.\d+)?\s*(mib|kib|gib|mb|kb|gb)" ]), "Stats output found in proof.txt", "No stats evidence found in proof.txt"),
        (any(re.search(p, content) for p in [r"nginx\s+version", r"nginx/\d+\.\d+"]), "Exec output (nginx version) found in proof.txt", "No exec evidence found in proof.txt"),
    ]
    for valid, success, error in checks:
        (successes if valid else errors).append(success if valid else error)
    return all(valid for valid, _, _ in checks), successes, errors


def _validate_part_a_deployment(container_name: str, host_port: int, container_port: int) -> Tuple[bool, List[str], List[str]]:
    successes = []
    errors = []
    if not _image_exists(REQUIRED_IMAGE):
        return False, successes, [f"{REQUIRED_IMAGE} image not found!", f"  -> Pull it: docker pull {REQUIRED_IMAGE}"]
    successes.append(f"{REQUIRED_IMAGE} image found locally")
    if not _container_exists(container_name):
        return False, successes, [f"Container '{container_name}' not found!", f"  -> Run it: docker run -d --name {container_name} -p {host_port}:{container_port} {REQUIRED_IMAGE}"]
    if not _container_running(container_name):
        return False, successes, [f"Container '{container_name}' exists but is NOT running!", f"  -> Start it: docker start {container_name}"]
    successes.append(f"Container '{container_name}' is running")
    actual_image = _get_container_image(container_name)
    if actual_image and not actual_image.startswith("nginx:alpine"):
        return False, successes, [f"Container using wrong image: {actual_image}", f"  -> Must use {REQUIRED_IMAGE}"]
    mapped_port = _container_port(container_name, str(container_port))
    if mapped_port != str(host_port):
        return False, successes, [f"Wrong port mapping: host port {mapped_port} instead of {host_port}", f"  -> Must use -p {host_port}:{container_port}"]
    successes.append(f"Port mapping {host_port}:{container_port} configured correctly")
    if not _check_port_with_curl(host_port):
        return False, successes, [f"Page not accessible at localhost:{host_port}"]
    successes.append(f"Page accessible at localhost:{host_port}")
    return True, successes, errors


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    all_errors = []
    warnings = []
    successes = []
    part_a_complete = False
    part_b_complete = False
    part_c_complete = False

    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available: {info}"

    rendu_path = _rendu_dir(exercise_path)
    rendu_path.mkdir(parents=True, exist_ok=True)
    container_exists = _container_exists(CONTAINER_NAME)
    container_running = _container_running(CONTAINER_NAME) if container_exists else False
    image_exists = _image_exists(REQUIRED_IMAGE)
    proof_file_exists = (rendu_path / "proof.txt").exists()
    proof_is_valid = _validate_proof_file(rendu_path)[0] if proof_file_exists else False

    if container_running:
        part_a_valid, part_a_successes, part_a_errors = _validate_part_a_deployment(CONTAINER_NAME, HOST_PORT, CONTAINER_PORT)
        if part_a_valid:
            successes.append("Part A Complete: Container deployed correctly")
            successes.extend([f"   • {s}" for s in part_a_successes])
            part_a_complete = True
        else:
            all_errors.extend(part_a_errors)
    elif container_exists:
        if proof_is_valid:
            part_a_complete = True
            successes.append("Part A: Deployment completed (valid proof.txt confirms it)")
            warnings.append(f"Container '{CONTAINER_NAME}' is stopped; remove it to finish.")
        else:
            all_errors.append(f"Container '{CONTAINER_NAME}' is stopped and proof.txt is incomplete.")
    elif image_exists and proof_is_valid:
        part_a_complete = True
        successes.append("Part A: Deployment completed (valid proof.txt confirms it)")
    elif image_exists:
        all_errors.append(f"Run: docker run -d --name {CONTAINER_NAME} -p {HOST_PORT}:{CONTAINER_PORT} {REQUIRED_IMAGE}")
    else:
        all_errors.append(f"Pull the image: docker pull {REQUIRED_IMAGE}")

    if proof_file_exists:
        proof_valid, proof_successes, proof_errors = _validate_proof_file(rendu_path)
        if proof_valid:
            successes.append("Part B Complete: proof.txt validated")
            successes.extend([f"   • {s}" for s in proof_successes])
            part_b_complete = True
        else:
            all_errors.extend(proof_errors)
    elif container_running:
        warnings.append(f"Save diagnostics to: {rendu_path / 'proof.txt'}")
    else:
        all_errors.append("proof.txt not found; complete diagnostics before removing the container.")

    if not container_exists:
        if part_a_complete and part_b_complete:
            part_c_complete = True
            successes.append(f"Part C Complete: Container '{CONTAINER_NAME}' properly removed")
    elif not container_running:
        all_errors.append(f"Container '{CONTAINER_NAME}' is a ghost; remove it with docker rm {CONTAINER_NAME}")

    if part_a_complete and part_b_complete and part_c_complete:
        return True, "Lab 01 Complete! Full container lifecycle mastered."

    lines = []
    if all_errors:
        lines.append("Validation Issues:\n- " + "\n- ".join(all_errors))
    if successes:
        lines.append("Completed:\n- " + "\n- ".join(successes))
    if warnings:
        lines.append("Notes:\n- " + "\n- ".join(warnings))
    return False, "\n\n".join(lines)
