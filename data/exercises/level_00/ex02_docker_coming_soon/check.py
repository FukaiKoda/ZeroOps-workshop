"""Interactive Docker validation for Lab 02: Coming Soon.

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


# ============================================================
# Constants
# ============================================================

REQUIRED_IMAGE = "nginx:alpine"
CONTAINER_NAME = "coming-soon"
HOST_PORT = 8080
CONTAINER_PORT = 80


# ============================================================
# Utility Functions
# ============================================================

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
    code, out, err = _run_command(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=10)
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
    code, out, _ = _run_command([
        "docker", "inspect",
        "--format", "{{.State.Running}}",
        name
    ])
    return code == 0 and out.lower() == "true"


def _get_container_image(name: str) -> Optional[str]:
    """Get the exact image name used by a container."""
    code, out, _ = _run_command([
        "docker", "inspect",
        "--format", "{{.Config.Image}}",
        name
    ])
    if code != 0:
        return None
    return out


def _container_port(name: str, container_port: str = "80") -> Optional[str]:
    """Get host port mapped to container port."""
    code, out, _ = _run_command([
        "docker", "inspect",
        "--format", f"{{{{(index (index .NetworkSettings.Ports \"{container_port}/tcp\") 0).HostPort}}}}",
        name
    ])
    if code != 0 or not out or out == "<no value>":
        return None
    return out


def _check_port_with_curl(port: int) -> bool:
    """Check if a port is accessible using curl (more reliable than raw socket)."""
    code, _, _ = _run_command(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"http://localhost:{port}"], timeout=5)
    return code == 0


# ============================================================
# Proof File Validation
# ============================================================

def _validate_proof_file(rendu_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Validate the proof.txt file for Part B (diagnostics).
    
    Returns: (valid, successes, errors)
    """
    proof_file = rendu_path / "proof.txt"
    successes = []
    errors = []
    
    if not proof_file.exists():
        errors.append("proof.txt not found in submission directory.")
        errors.append(f"  → Create it at: {proof_file}")
        errors.append("  → Save output of diagnostic commands:")
        errors.append("    docker logs --tail 10 coming-soon >> proof.txt")
        errors.append("    docker stats --no-stream coming-soon >> proof.txt")
        errors.append("    docker exec coming-soon nginx -v 2>> proof.txt")
        return False, successes, errors
    
    try:
        content = proof_file.read_text().lower()
    except Exception as e:
        errors.append(f"Could not read proof.txt: {e}")
        return False, successes, errors
    
    if not content.strip():
        errors.append("proof.txt is empty")
        return False, successes, errors
    
    # Check for logs evidence
    logs_patterns = [
        r"nginx",
        r"\d{4}/\d{2}/\d{2}",  # Date pattern in logs
        r"start\s*(worker|master)",
        r"listening",
    ]
    has_logs = any(re.search(p, content) for p in logs_patterns)
    
    if has_logs:
        successes.append("Logs output found in proof.txt")
    else:
        errors.append("No logs evidence found in proof.txt")
        errors.append("  → Run: docker logs --tail 10 coming-soon >> proof.txt")
    
    # Check for stats evidence
    stats_patterns = [
        r"cpu\s*%",
        r"mem\s*(usage|%)",
        r"container\s+id",
        r"net\s+i/o",
        r"\d+\.\d+%",  # Percentage pattern
        r"\d+(\.\d+)?\s*(mib|kib|gib|mb|kb|gb)",  # Memory pattern
    ]
    has_stats = any(re.search(p, content) for p in stats_patterns)
    
    if has_stats:
        successes.append("Stats output found in proof.txt")
    else:
        errors.append("No stats evidence found in proof.txt")
        errors.append("  → Run: docker stats --no-stream coming-soon >> proof.txt")
    
    # Check for exec evidence (nginx version)
    exec_patterns = [
        r"nginx\s+version",
        r"nginx/\d+\.\d+",
    ]
    has_exec = any(re.search(p, content) for p in exec_patterns)
    
    if has_exec:
        successes.append("Exec output (nginx version) found in proof.txt")
    else:
        errors.append("No exec evidence found in proof.txt")
        errors.append("  → Run: docker exec coming-soon nginx -v >> proof.txt")
    
    valid = has_logs and has_stats and has_exec
    return valid, successes, errors


# ============================================================
# Part A Validation: Container Deployment
# ============================================================

def _validate_part_a_deployment(container_name: str, host_port: int, container_port: int) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Part A: Container deployment requirements.
    
    Checks:
    1. nginx:alpine image exists
    2. Container 'coming-soon' is running
    3. Port mapping 8080:80 is correct
    4. Page is accessible via curl
    
    Returns: (valid, successes, errors)
    """
    successes = []
    errors = []
    
    # Check 1: Image exists
    if not _image_exists(REQUIRED_IMAGE):
        errors.append(f"{REQUIRED_IMAGE} image not found!")
        errors.append(f"  → Pull it: docker pull {REQUIRED_IMAGE}")
        return False, successes, errors
    
    successes.append(f"{REQUIRED_IMAGE} image found locally")
    
    # Check 2: Container exists and is running
    if not _container_exists(container_name):
        errors.append(f"Container '{container_name}' not found!")
        errors.append(f"  → Run it: docker run -d --name {container_name} -p {host_port}:{container_port} {REQUIRED_IMAGE}")
        return False, successes, errors
    
    if not _container_running(container_name):
        errors.append(f"Container '{container_name}' exists but is NOT running!")
        errors.append(f"  → Start it: docker start {container_name}")
        errors.append(f"  → Or remove and re-run: docker rm {container_name} && docker run -d --name {container_name} -p {host_port}:{container_port} {REQUIRED_IMAGE}")
        return False, successes, errors
    
    successes.append(f"Container '{container_name}' is running")
    
    # Check 3: Correct image used
    actual_image = _get_container_image(container_name)
    if actual_image and not actual_image.startswith("nginx:alpine"):
        errors.append(f"Container using wrong image: {actual_image}")
        errors.append(f"  → Must use {REQUIRED_IMAGE}")
        errors.append(f"  → Remove and re-run: docker rm -f {container_name} && docker run -d --name {container_name} -p {host_port}:{container_port} {REQUIRED_IMAGE}")
        return False, successes, errors
    
    # Check 4: Port mapping
    mapped_port = _container_port(container_name, str(container_port))
    if mapped_port is None:
        errors.append(f"No port mapping found for container port {container_port}")
        errors.append(f"  → Container must map port {host_port}:{container_port}")
        errors.append(f"  → Remove and re-run: docker rm -f {container_name} && docker run -d --name {container_name} -p {host_port}:{container_port} {REQUIRED_IMAGE}")
        return False, successes, errors
    
    if mapped_port != str(host_port):
        errors.append(f"Wrong port mapping: host port {mapped_port} instead of {host_port}")
        errors.append(f"  → Must use -p {host_port}:{container_port}")
        errors.append(f"  → Remove and re-run: docker rm -f {container_name} && docker run -d --name {container_name} -p {host_port}:{container_port} {REQUIRED_IMAGE}")
        return False, successes, errors
    
    successes.append(f"Port mapping {host_port}:{container_port} configured correctly")
    
    # Check 5: Page accessible
    if not _check_port_with_curl(host_port):
        errors.append(f"Page not accessible at localhost:{host_port}")
        errors.append("  → Check if container is running: docker ps")
        errors.append("  → Check container logs: docker logs coming-soon")
        return False, successes, errors
    
    successes.append(f"Page accessible at localhost:{host_port}")
    
    return True, successes, errors


# ============================================================
# Main Grade Function
# ============================================================

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grade Lab 02: Coming Soon - Container Lifecycle.
    
    Validates:
    1. Part A: Container deployed correctly (image, name, ports, accessible)
    2. Part B: proof.txt exists with diagnostic output
    3. Part C: Container 'coming-soon' has been removed (lifecycle complete)
    
    The grader detects the current state:
    - If container is running: validates Part A fully, checks Part B
    - If container is removed + proof.txt exists: validates full completion
    """
    all_errors = []
    warnings = []
    successes = []
    part_a_complete = False
    part_b_complete = False
    part_c_complete = False
    
    # Check Docker availability
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available: {info}"
    
    # Determine submission directory
    rendu_path = _rendu_dir(exercise_path)
    
    # Create rendu directory if it doesn't exist
    if not rendu_path.exists():
        try:
            rendu_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            all_errors.append(f"Could not create submission directory: {e}")
            return False, "Validation failed:\n- " + "\n- ".join(all_errors)
    
    # ─────────────────────────────────────────────────────────
    # Detect current state: Is container running or removed?
    # ─────────────────────────────────────────────────────────
    container_exists = _container_exists(CONTAINER_NAME)
    container_running = _container_running(CONTAINER_NAME) if container_exists else False
    image_exists = _image_exists(REQUIRED_IMAGE)
    proof_file_exists = (rendu_path / "proof.txt").exists()
    
    # Pre-validate proof.txt to check if it's actually valid (not just exists)
    proof_is_valid = False
    if proof_file_exists:
        proof_valid_check, _, _ = _validate_proof_file(rendu_path)
        proof_is_valid = proof_valid_check
    
    # ─────────────────────────────────────────────────────────
    # Part A: Deployment Validation
    # ─────────────────────────────────────────────────────────
    if container_running:
        # Container is running - validate Part A fully
        part_a_valid, part_a_successes, part_a_errors = _validate_part_a_deployment(
            CONTAINER_NAME, HOST_PORT, CONTAINER_PORT
        )
        
        if part_a_valid:
            successes.append("✅ Part A Complete: Container deployed correctly")
            successes.extend([f"   • {s}" for s in part_a_successes])
            part_a_complete = True
        else:
            all_errors.append("❌ Part A: Deployment issues found")
            all_errors.extend(part_a_errors)
    
    elif container_exists and not container_running:
        # Container exists but stopped - needs to be running for Part A or removed for Part C
        if not proof_is_valid:
            all_errors.append(f"❌ Part A: Container '{CONTAINER_NAME}' is stopped!")
            all_errors.append("  → Start it to continue Part A: docker start coming-soon")
            all_errors.append(f"  → Then verify page: curl localhost:{HOST_PORT}")
        else:
            # proof.txt is VALID, container stopped = user completed Part A/B, forgot to remove
            part_a_complete = True
            successes.append("✅ Part A: Deployment was completed (valid proof.txt confirms container was run)")
            warnings.append(f"⚠️  Container '{CONTAINER_NAME}' is stopped (ghost container)")
            warnings.append("  → Complete Part C by removing it: docker rm coming-soon")
    
    elif not container_exists:
        # Container removed - check if Part A was completed (evidence: image + VALID proof.txt)
        if image_exists and proof_is_valid:
            # User completed the full lifecycle - Part A was done
            # VALID proof.txt proves they ran the container and did diagnostics correctly
            part_a_complete = True
            successes.append("✅ Part A: Deployment completed (valid proof.txt confirms container was run)")
        elif image_exists:
            # Image exists but no container and no valid proof - user only pulled the image!
            all_errors.append("❌ Part A: Image pulled but container not running!")
            all_errors.append(f"  → You pulled the image but didn't run the container")
            all_errors.append(f"  → Run: docker run -d --name {CONTAINER_NAME} -p {HOST_PORT}:{CONTAINER_PORT} {REQUIRED_IMAGE}")
            all_errors.append(f"  → Then verify: curl localhost:{HOST_PORT}")
        else:
            # No image, no container - hasn't started
            all_errors.append(f"❌ Part A: {REQUIRED_IMAGE} image not found!")
            all_errors.append(f"  → Pull the image: docker pull {REQUIRED_IMAGE}")
            all_errors.append(f"  → Then run: docker run -d --name {CONTAINER_NAME} -p {HOST_PORT}:{CONTAINER_PORT} {REQUIRED_IMAGE}")
    
    # ─────────────────────────────────────────────────────────
    # Part B: Diagnostics Evidence (proof.txt)
    # ─────────────────────────────────────────────────────────
    if proof_file_exists:
        proof_valid, proof_successes, proof_errors = _validate_proof_file(rendu_path)
        
        if proof_valid:
            successes.append("✅ Part B Complete: proof.txt validated")
            successes.extend([f"   • {s}" for s in proof_successes])
            part_b_complete = True
        else:
            all_errors.append("❌ Part B: proof.txt incomplete")
            all_errors.extend(proof_errors)
    else:
        if container_running:
            # Container running, no proof.txt yet - expected state during Part B
            warnings.append("Part B: proof.txt not found yet")
            warnings.append(f"  → Save diagnostics to: {rendu_path / 'proof.txt'}")
            warnings.append("  → Run these commands:")
            warnings.append(f"    cd {rendu_path}")
            warnings.append("    docker logs --tail 10 coming-soon >> proof.txt")
            warnings.append("    docker stats --no-stream coming-soon >> proof.txt")
            warnings.append("    docker exec coming-soon nginx -v >> proof.txt 2>&1")
        elif not container_exists and image_exists:
            all_errors.append("❌ Part B: proof.txt not found!")
            all_errors.append("  → You removed the container before saving diagnostics")
            all_errors.append(f"  → Re-run container: docker run -d --name {CONTAINER_NAME} -p {HOST_PORT}:{CONTAINER_PORT} {REQUIRED_IMAGE}")
            all_errors.append("  → Then complete Part B and save proof.txt")
    
    # ─────────────────────────────────────────────────────────
    # Part C: Lifecycle Evidence (container removed)
    # ─────────────────────────────────────────────────────────
    if not container_exists:
        if part_a_complete and part_b_complete:
            successes.append(f"✅ Part C Complete: Container '{CONTAINER_NAME}' properly removed")
            part_c_complete = True
        elif part_a_complete:
            # Container removed but Part B not complete
            pass  # Already handled above
    elif container_running:
        # Container still running - Part C not done (this is expected during Parts A/B)
        pass
    else:
        # Container exists but stopped - ghost container
        all_errors.append(f"❌ Part C: Container '{CONTAINER_NAME}' is a ghost (stopped but not removed)")
        all_errors.append("  → Remove it: docker rm coming-soon")
    
    # ─────────────────────────────────────────────────────────
    # Build Result
    # ─────────────────────────────────────────────────────────
    
    # Determine overall status
    if part_a_complete and part_b_complete and part_c_complete:
        # Full completion!
        success_msg = """✅ Lab 02 Complete! Full container lifecycle mastered!

You've successfully demonstrated:
• Pulling images (docker pull)
• Running containers in detached mode (-d)
• Port mapping (-p 8080:80)
• Naming containers (--name coming-soon)
• Viewing logs (docker logs)
• Monitoring resources (docker stats)
• Executing commands (docker exec)
• Container lifecycle (stop/start/rm)

Clean workspace confirmed - no ghost containers! 🚀

➡️ Proceed to Lab 03: The Blueprint"""
        return True, success_msg
    
    # Partial completion or errors
    lines = []
    
    if all_errors:
        lines.append("❌ Validation Issues:\n")
        for err in all_errors:
            lines.append(f"  {err}")
        lines.append("")
    
    if successes:
        lines.append("✅ Completed:\n")
        for s in successes:
            lines.append(f"  {s}")
        lines.append("")
    
    if warnings:
        lines.append("⚠️ Notes:\n")
        for w in warnings:
            lines.append(f"  {w}")
        lines.append("")
    
    # Show next steps based on current state
    lines.append("📋 Progress:")
    lines.append(f"  Part A (Deployment):  {'✅' if part_a_complete else '❌'}")
    lines.append(f"  Part B (Diagnostics): {'✅' if part_b_complete else '❌'}")
    lines.append(f"  Part C (Cleanup):     {'✅' if part_c_complete else '❌'}")
    
    return False, "\n".join(lines)
