"""Interactive Docker Compose validation for Lab 08: The Orchestra.

Goal:
Validate Docker Compose setup with multi-service orchestration:
1. docker-compose.yml file exists and is valid
2. Services defined correctly (web + db)
3. Volumes, ports, and environment configured properly
4. Compose stack can be started and verified

Final expected state:
- docker-compose.yml exists in submission directory
- Services 'web' and 'db' are properly defined
- Stack can be validated with docker compose config
"""

from __future__ import annotations

import re
import subprocess
import json
import yaml
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any


# ============================================================
# Constants
# ============================================================

COMPOSE_FILE = "docker-compose.yml"
REQUIRED_SERVICES = ["web", "db"]
WEB_IMAGE = "nginx:alpine"
DB_IMAGE = "postgres:15-alpine"
WEB_PORT = 8080
DB_VOLUME = "db-data"


# ============================================================
# Utility Functions
# ============================================================

def _rendu_dir(exercise_path: Path) -> Path:
    """Get the user's submission directory."""
    return Path.home() / "rendudevops" / exercise_path.name


def _run_command(args: list[str], timeout: int = 30, cwd: Path = None) -> Tuple[int, str, str]:
    """Execute a command and return exit code, stdout, stderr."""
    try:
        proc = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
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


def _compose_available() -> Tuple[bool, str]:
    """Check if Docker Compose is available."""
    code, out, err = _run_command(["docker", "compose", "version"], timeout=10)
    if code != 0:
        return False, err or out or "Docker Compose is not available"
    return True, out


# ============================================================
# Compose File Validation
# ============================================================

def _validate_compose_file(compose_path: Path) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Validate the docker-compose.yml file structure and content.
    
    Returns: (valid, parsed_data, errors)
    """
    errors = []
    
    if not compose_path.exists():
        return False, {}, [f"docker-compose.yml not found at {compose_path}"]
    
    # Try to parse YAML
    try:
        with open(compose_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, {}, [f"Invalid YAML syntax: {e}"]
    
    if not isinstance(data, dict):
        return False, {}, ["docker-compose.yml must be a YAML dictionary"]
    
    # Check for 'services' key
    if "services" not in data:
        errors.append("Missing 'services' key in compose file")
        return False, data, errors
    
    services = data.get("services", {})
    
    return len(errors) == 0, data, errors


def _validate_web_service(services: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate the 'web' service configuration.
    
    Returns: (valid, successes, errors)
    """
    successes = []
    errors = []
    
    if "web" not in services:
        return False, [], ["Service 'web' not defined in compose file"]
    
    web = services["web"]
    
    # Check image
    image = web.get("image", "")
    if image == WEB_IMAGE:
        successes.append(f"Web service uses correct image: {WEB_IMAGE}")
    elif "nginx" in image.lower():
        errors.append(f"Web service should use '{WEB_IMAGE}', got '{image}'")
    else:
        errors.append(f"Web service missing or wrong image (expected '{WEB_IMAGE}')")
    
    # Check ports
    ports = web.get("ports", [])
    port_mapping_found = False
    for port in ports:
        port_str = str(port)
        if "8080:80" in port_str or ("8080" in port_str and "80" in port_str):
            port_mapping_found = True
            successes.append("Web service port mapping: 8080 → 80")
            break
    
    if not port_mapping_found:
        errors.append("Web service should map host port 8080 to container port 80")
        errors.append("  → Add: ports: ['8080:80']")
    
    # Check volumes (bind mount for index.html)
    volumes = web.get("volumes", [])
    has_index_mount = False
    for vol in volumes:
        vol_str = str(vol)
        if "index.html" in vol_str and "/usr/share/nginx/html" in vol_str:
            has_index_mount = True
            successes.append("Web service has index.html bind mount")
            break
    
    if not has_index_mount:
        errors.append("Web service should bind mount ./index.html to /usr/share/nginx/html/index.html")
        errors.append("  → Add: volumes: ['./index.html:/usr/share/nginx/html/index.html']")
    
    return len(errors) == 0, successes, errors


def _validate_db_service(services: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate the 'db' service configuration.
    
    Returns: (valid, successes, errors)
    """
    successes = []
    errors = []
    
    if "db" not in services:
        return False, [], ["Service 'db' not defined in compose file"]
    
    db = services["db"]
    
    # Check image
    image = db.get("image", "")
    if image == DB_IMAGE:
        successes.append(f"DB service uses correct image: {DB_IMAGE}")
    elif "postgres" in image.lower():
        successes.append(f"DB service uses PostgreSQL image: {image}")
    else:
        errors.append(f"DB service missing or wrong image (expected '{DB_IMAGE}')")
    
    # Check environment variables
    env = db.get("environment", {})
    env_list = []
    
    # Handle both list and dict format
    if isinstance(env, list):
        env_list = env
        env = {}
        for item in env_list:
            if "=" in str(item):
                key, value = str(item).split("=", 1)
                env[key] = value
    
    if "POSTGRES_PASSWORD" in env or any("POSTGRES_PASSWORD" in str(e) for e in env_list):
        successes.append("DB service has POSTGRES_PASSWORD set")
    else:
        errors.append("DB service missing POSTGRES_PASSWORD environment variable")
        errors.append("  → Add: environment: [POSTGRES_PASSWORD=secretpass]")
    
    if "POSTGRES_DB" in env or any("POSTGRES_DB" in str(e) for e in env_list):
        successes.append("DB service has POSTGRES_DB set")
    else:
        errors.append("DB service missing POSTGRES_DB environment variable")
        errors.append("  → Add: environment: [POSTGRES_DB=grademe]")
    
    # Check volumes (named volume for data persistence)
    volumes = db.get("volumes", [])
    has_data_volume = False
    for vol in volumes:
        vol_str = str(vol)
        if "/var/lib/postgresql/data" in vol_str:
            has_data_volume = True
            if vol_str.startswith("./") or vol_str.startswith("/"):
                errors.append("DB volume should be a named volume, not a bind mount")
                errors.append("  → Use: 'db-data:/var/lib/postgresql/data'")
            else:
                successes.append("DB service has named volume for data persistence")
            break
    
    if not has_data_volume:
        errors.append("DB service should mount a volume to /var/lib/postgresql/data")
        errors.append("  → Add: volumes: ['db-data:/var/lib/postgresql/data']")
    
    return len(errors) == 0, successes, errors


def _validate_top_level_volumes(data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate top-level volumes declaration.
    
    Returns: (valid, successes, errors)
    """
    successes = []
    errors = []
    
    volumes = data.get("volumes", {})
    
    if "db-data" in volumes or DB_VOLUME in volumes:
        successes.append(f"Named volume '{DB_VOLUME}' declared at top level")
    else:
        # Check if any volume name containing 'db' or 'data' exists
        found = any("db" in v.lower() or "data" in v.lower() for v in volumes.keys())
        if found:
            successes.append("Named volume for database declared")
        else:
            errors.append(f"Missing top-level volume declaration for '{DB_VOLUME}'")
            errors.append("  → Add at the end of your compose file:")
            errors.append("    volumes:")
            errors.append("      db-data:")
    
    return len(errors) == 0, successes, errors


def _validate_compose_syntax(compose_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate compose file with docker compose config.
    
    Returns: (valid, errors)
    """
    code, out, err = _run_command(
        ["docker", "compose", "-f", str(compose_path), "config", "--quiet"],
        cwd=compose_path.parent
    )
    
    if code != 0:
        return False, [f"Compose validation failed: {err[:300]}"]
    
    return True, []


def _validate_index_html(rendu_path: Path) -> Tuple[bool, List[str]]:
    """Validate that index.html exists."""
    index_path = rendu_path / "index.html"
    
    if not index_path.exists():
        return False, [
            "index.html not found in submission directory",
            f"  → Create it at: {index_path}",
            "  → Or copy the provided template"
        ]
    
    try:
        content = index_path.read_text()
        if len(content.strip()) < 20:
            return False, ["index.html appears to be too short or empty"]
    except Exception as e:
        return False, [f"Could not read index.html: {e}"]
    
    return True, []


def _check_stack_running(rendu_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Check if the compose stack is currently running.
    
    Returns: (running, successes, errors)
    """
    successes = []
    errors = []
    
    code, out, err = _run_command(
        ["docker", "compose", "ps", "--format", "json"],
        cwd=rendu_path
    )
    
    if code != 0:
        return False, [], ["Could not check running services"]
    
    if not out.strip():
        return False, [], ["No services currently running"]
    
    try:
        # Parse JSON output (may be multiple lines for multiple containers)
        containers = []
        for line in out.strip().splitlines():
            if line.strip():
                containers.append(json.loads(line))
        
        web_running = any("web" in c.get("Name", "").lower() for c in containers)
        db_running = any("db" in c.get("Name", "").lower() for c in containers)
        
        if web_running:
            successes.append("Web service is running")
        if db_running:
            successes.append("DB service is running")
        
        if web_running and db_running:
            return True, successes, []
        else:
            if not web_running:
                errors.append("Web service is not running")
            if not db_running:
                errors.append("DB service is not running")
            return False, successes, errors
            
    except json.JSONDecodeError:
        # Fallback: check text output
        if "web" in out.lower() and "db" in out.lower():
            return True, ["Services appear to be running"], []
        return False, [], ["Could not parse service status"]


# ============================================================
# Default Files
# ============================================================

DEFAULT_INDEX_HTML = """<!DOCTYPE html>
<html>
<head><title>Grade Me System</title></head>
<body>
    <h1>🎓 Grade Me System</h1>
    <p>Status: <strong>Online</strong></p>
    <p>Database: <span id="db">Checking...</span></p>
</body>
</html>
"""


def _ensure_index_html(rendu_path: Path) -> None:
    """Auto-create index.html if it doesn't exist."""
    index_path = rendu_path / "index.html"
    if not index_path.exists():
        try:
            rendu_path.mkdir(parents=True, exist_ok=True)
            index_path.write_text(DEFAULT_INDEX_HTML)
        except Exception:
            pass


# ============================================================
# Main Grade Function
# ============================================================

def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grade Lab 08: The Orchestra - Docker Compose.
    
    Validates:
    1. docker-compose.yml exists and is valid YAML
    2. 'web' service is properly configured (nginx, ports, volumes)
    3. 'db' service is properly configured (postgres, env, volumes)
    4. Named volumes are declared
    5. Compose syntax validates with docker compose config
    
    Bonus: Check if stack is running
    """
    all_errors = []
    warnings = []
    successes = []
    
    # Check Docker availability
    ok, info = _docker_available()
    if not ok:
        return False, f"Docker is not available: {info}"
    
    # Check Compose availability
    ok, info = _compose_available()
    if not ok:
        return False, f"Docker Compose is not available: {info}"
    
    # Determine submission directory
    rendu_path = _rendu_dir(exercise_path)
    
    # Create rendu directory if it doesn't exist
    if not rendu_path.exists():
        try:
            rendu_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            all_errors.append(f"Could not create submission directory: {e}")
            return False, "Validation failed:\n- " + "\n- ".join(all_errors)
    
    # Auto-create index.html
    _ensure_index_html(rendu_path)
    
    compose_path = rendu_path / COMPOSE_FILE
    
    # ─────────────────────────────────────────────────────────
    # Part A: Compose File Exists and Valid YAML
    # ─────────────────────────────────────────────────────────
    valid, data, errors = _validate_compose_file(compose_path)
    
    if not valid or not data:
        all_errors.extend(errors)
        all_errors.append("")
        all_errors.append("Create your docker-compose.yml at:")
        all_errors.append(f"  {compose_path}")
        return False, "Validation failed:\n- " + "\n- ".join(all_errors)
    
    successes.append("docker-compose.yml found and valid YAML")
    
    services = data.get("services", {})
    
    # ─────────────────────────────────────────────────────────
    # Part A: Web Service Configuration
    # ─────────────────────────────────────────────────────────
    web_valid, web_successes, web_errors = _validate_web_service(services)
    successes.extend(web_successes)
    all_errors.extend(web_errors)
    
    # ─────────────────────────────────────────────────────────
    # Part B: DB Service Configuration
    # ─────────────────────────────────────────────────────────
    db_valid, db_successes, db_errors = _validate_db_service(services)
    successes.extend(db_successes)
    all_errors.extend(db_errors)
    
    # ─────────────────────────────────────────────────────────
    # Volume Declaration
    # ─────────────────────────────────────────────────────────
    vol_valid, vol_successes, vol_errors = _validate_top_level_volumes(data)
    successes.extend(vol_successes)
    all_errors.extend(vol_errors)
    
    # ─────────────────────────────────────────────────────────
    # Compose Syntax Validation
    # ─────────────────────────────────────────────────────────
    syntax_valid, syntax_errors = _validate_compose_syntax(compose_path)
    if syntax_valid:
        successes.append("Compose file passes docker compose config validation")
    else:
        all_errors.extend(syntax_errors)
    
    # ─────────────────────────────────────────────────────────
    # index.html check
    # ─────────────────────────────────────────────────────────
    html_valid, html_errors = _validate_index_html(rendu_path)
    if html_valid:
        successes.append("index.html exists")
    else:
        warnings.extend(html_errors)
    
    # ─────────────────────────────────────────────────────────
    # Bonus: Check if stack is running
    # ─────────────────────────────────────────────────────────
    running, run_successes, run_errors = _check_stack_running(rendu_path)
    if running:
        successes.extend(run_successes)
        successes.append("Stack is running! Test at http://localhost:8080")
    else:
        warnings.append("Stack is not currently running")
        warnings.append("  → Start with: docker compose up -d")
    
    # ─────────────────────────────────────────────────────────
    # Build Result
    # ─────────────────────────────────────────────────────────
    if all_errors:
        error_msg = "Validation failed:\n- " + "\n- ".join(all_errors)
        if successes:
            error_msg += "\n\n✅ Completed:\n- " + "\n- ".join(successes)
        if warnings:
            error_msg += "\n\n⚠️ Warnings:\n- " + "\n- ".join(warnings)
        return False, error_msg
    
    success_msg = """✅ Lab 08 Complete! Docker Compose mastered!

You've successfully demonstrated:
• Writing a docker-compose.yml from scratch
• Defining multiple services (web + db)
• Port mapping in Compose syntax
• Bind mounts for static files
• Named volumes for data persistence
• Environment variable configuration
• Compose stack lifecycle (up/down)

One file to rule them all! 🎼

➡️ You've completed Level 00: Docker Fundamentals!
➡️ Proceed to Level 01: Kubernetes Basics"""
    
    if warnings:
        success_msg += "\n\n⚠️ Notes:\n- " + "\n- ".join(warnings)
    
    return True, success_msg
