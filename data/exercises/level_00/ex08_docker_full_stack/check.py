"""
Lab 09 Grader: The Full Stack
Multi-Service Application Validation

Validates:
- docker-compose.yml structure and validity
- All required source files exist
- Services are running with correct configuration
- Inter-service communication works
- API endpoints respond correctly
- Database is initialized and queryable
"""

from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import subprocess
import socket
import json
import yaml
import re
import time


# ============================================================
# SECTION 1: Configuration
# ============================================================

class Lab09Config:
    """Lab 09 specific configuration."""
    
    LAB_NUMBER = "09"
    LAB_TITLE = "The Full Stack"
    
    # Expected services
    SERVICES = {
        "frontend": {
            "build_context": "./frontend",
            "ports": {"80/tcp": "8080"},
            "image_contains": "lab-09",  # Compose naming convention
        },
        "backend": {
            "build_context": "./backend",
            "ports": {"5000/tcp": "5000"},
            "env_required": ["DB_HOST", "DB_PASSWORD"],
            "image_contains": "lab-09",
        },
        "db": {
            "image": "postgres:15-alpine",
            "env_required": ["POSTGRES_PASSWORD", "POSTGRES_DB"],
            "volume_mount": "/var/lib/postgresql/data",
        },
    }
    
    # Expected files
    REQUIRED_FILES = [
        "docker-compose.yml",
        "frontend/Dockerfile",
        "frontend/index.html",
        "backend/Dockerfile",
        "backend/app.py",
        "backend/requirements.txt",
        "database/init.sql",
    ]
    
    # Expected volume
    VOLUME_NAME = "db-data"  # or lab-09_db-data with compose prefix
    
    # API endpoints to test
    ENDPOINTS = {
        "frontend": ("http://localhost:8080", 200, "Grade Me"),
        "backend_health": ("http://localhost:5000/health", 200, "healthy"),
        "backend_api": ("http://localhost:5000/submissions", 200, "Alice"),
    }
    
    # Scoring
    PASSING_PERCENTAGE = 80


# ============================================================
# SECTION 2: Utility Functions
# ============================================================

def run_cmd(args: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """Execute command and return (exit_code, stdout, stderr)."""
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
        return 127, "", "Command not found"


def docker_available() -> Tuple[bool, str]:
    """Check if Docker daemon is running."""
    code, out, err = run_cmd(["docker", "info", "--format", "{{.ServerVersion}}"])
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


def docker_inspect(resource_type: str, name: str) -> Tuple[bool, dict]:
    """Inspect a Docker resource and return (exists, data)."""
    code, out, _ = run_cmd(["docker", resource_type, "inspect", name])
    if code != 0:
        return False, {}
    try:
        data = json.loads(out)
        return True, data[0] if data else {}
    except json.JSONDecodeError:
        return False, {}


def http_request(url: str, timeout: int = 5) -> Tuple[int, str]:
    """
    Make HTTP request and return (status_code, body).
    Returns (-1, error_message) on failure.
    """
    try:
        # Use curl for simplicity (available in most environments)
        code, out, err = run_cmd([
            "curl", "-s", "-o", "-", "-w", "\n%{http_code}",
            "--max-time", str(timeout), url
        ])
        
        if code != 0:
            return -1, err or "Request failed"
        
        lines = out.rsplit("\n", 1)
        if len(lines) == 2:
            body, status = lines
            return int(status), body
        return -1, "Unexpected response format"
    
    except Exception as e:
        return -1, str(e)


def port_accessible(port: int, host: str = "localhost") -> bool:
    """Check if a port is accessible."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


# ============================================================
# SECTION 3: Compose-Specific Utilities
# ============================================================

def get_compose_project_name(exercise_path: Path) -> str:
    """Get the compose project name (defaults to directory name)."""
    return exercise_path.name.lower().replace("-", "").replace("_", "")


def compose_config(exercise_path: Path) -> Tuple[bool, dict, str]:
    """
    Parse and validate docker-compose.yml using docker compose config.
    Returns (valid, parsed_config, error_message).
    """
    compose_file = exercise_path / "docker-compose.yml"
    
    if not compose_file.exists():
        return False, {}, "docker-compose.yml not found"
    
    code, out, err = run_cmd([
        "docker", "compose", "-f", str(compose_file), "config"
    ])
    
    if code != 0:
        return False, {}, f"Compose validation failed: {err}"
    
    try:
        config = yaml.safe_load(out)
        return True, config, ""
    except yaml.YAMLError as e:
        return False, {}, f"Failed to parse compose config: {e}"


def compose_ps(exercise_path: Path) -> Tuple[bool, List[dict], str]:
    """
    Get running services status.
    Returns (success, services_list, error_message).
    """
    compose_file = exercise_path / "docker-compose.yml"
    
    code, out, err = run_cmd([
        "docker", "compose", "-f", str(compose_file), 
        "ps", "--format", "json"
    ])
    
    if code != 0:
        return False, [], err
    
    try:
        # Docker compose ps --format json outputs one JSON per line
        services = []
        for line in out.strip().split("\n"):
            if line.strip():
                services.append(json.loads(line))
        return True, services, ""
    except json.JSONDecodeError:
        # Fallback: try parsing as single JSON array
        try:
            services = json.loads(out)
            return True, services if isinstance(services, list) else [services], ""
        except:
            return False, [], "Failed to parse compose ps output"


def get_service_container_name(exercise_path: Path, service: str) -> Optional[str]:
    """Get the actual container name for a compose service."""
    success, services, _ = compose_ps(exercise_path)
    
    if not success:
        return None
    
    for svc in services:
        # Different docker compose versions use different keys
        svc_name = svc.get("Service") or svc.get("service") or ""
        if svc_name == service:
            return svc.get("Name") or svc.get("name") or svc.get("ID")
    
    return None


# ============================================================
# SECTION 4: Verification Functions
# ============================================================

def verify_docker_available() -> Tuple[bool, List[str]]:
    """Verify Docker is available."""
    ok, info = docker_available()
    if not ok:
        return False, [f"Docker not available: {info}"]
    return True, []


def verify_required_files(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify all required source files exist."""
    errors = []
    
    for file_path in Lab09Config.REQUIRED_FILES:
        full_path = exercise_path / file_path
        if not full_path.exists():
            errors.append(f"Missing file: {file_path}")
    
    return len(errors) == 0, errors


def verify_compose_file_structure(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify docker-compose.yml has correct structure."""
    errors = []
    
    compose_file = exercise_path / "docker-compose.yml"
    
    if not compose_file.exists():
        return False, ["docker-compose.yml not found"]
    
    # Parse YAML directly first
    try:
        with open(compose_file) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML syntax: {e}"]
    
    if not isinstance(config, dict):
        return False, ["docker-compose.yml must be a YAML dictionary"]
    
    # Check for services key
    if "services" not in config:
        errors.append("Missing 'services' key in docker-compose.yml")
        return False, errors
    
    services = config.get("services", {})
    
    # Check each required service
    for service_name, requirements in Lab09Config.SERVICES.items():
        if service_name not in services:
            errors.append(f"Missing service: '{service_name}'")
            continue
        
        svc = services[service_name]
        
        # Check build context (for frontend/backend)
        if "build_context" in requirements:
            if "build" not in svc:
                errors.append(f"Service '{service_name}' should use 'build:', not 'image:'")
            else:
                build = svc["build"]
                if isinstance(build, str):
                    if build != requirements["build_context"]:
                        errors.append(f"Service '{service_name}' build context should be '{requirements['build_context']}'")
                elif isinstance(build, dict):
                    ctx = build.get("context", "")
                    if ctx != requirements["build_context"]:
                        errors.append(f"Service '{service_name}' build context should be '{requirements['build_context']}'")
        
        # Check image (for db)
        if "image" in requirements:
            if svc.get("image") != requirements["image"]:
                actual = svc.get("image", "not specified")
                errors.append(f"Service '{service_name}' should use image '{requirements['image']}', got '{actual}'")
        
        # Check required environment variables
        if "env_required" in requirements:
            env = svc.get("environment", [])
            # Handle both list and dict format
            if isinstance(env, dict):
                env_keys = list(env.keys())
            else:
                env_keys = [e.split("=")[0] if "=" in e else e for e in env]
            
            for req_env in requirements["env_required"]:
                # Check if variable is present (with or without $ prefix)
                found = any(
                    req_env in key or req_env in key.replace("${", "").replace("}", "")
                    for key in env_keys
                )
                if not found and req_env not in str(env):
                    errors.append(f"Service '{service_name}' missing environment variable: {req_env}")
    
    # Check for volumes definition
    if "volumes" not in config:
        errors.append("Missing 'volumes' section (needed for db-data)")
    else:
        volumes = config.get("volumes", {})
        # Check for db-data volume (with possible variations)
        has_db_volume = any("db" in v.lower() and "data" in v.lower() for v in volumes.keys())
        if not has_db_volume and "db-data" not in volumes:
            errors.append("Missing named volume 'db-data' in volumes section")
    
    return len(errors) == 0, errors


def verify_compose_valid(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify docker-compose.yml passes docker compose config validation."""
    valid, _, error = compose_config(exercise_path)
    
    if not valid:
        return False, [f"Compose validation failed: {error}"]
    
    return True, []


def verify_services_running(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify all services are running."""
    errors = []
    
    success, services, err = compose_ps(exercise_path)
    
    if not success:
        return False, [f"Could not check services: {err}"]
    
    if not services:
        return False, ["No services running. Did you run 'docker compose up -d'?"]
    
    # Check each required service
    running_services = {}
    for svc in services:
        name = svc.get("Service") or svc.get("service") or ""
        state = svc.get("State") or svc.get("state") or ""
        health = svc.get("Health") or svc.get("health") or ""
        running_services[name] = {"state": state, "health": health}
    
    for service_name in Lab09Config.SERVICES.keys():
        if service_name not in running_services:
            errors.append(f"Service '{service_name}' is not running")
        else:
            state = running_services[service_name]["state"]
            if state.lower() not in ["running", "up"]:
                errors.append(f"Service '{service_name}' is not running (state: {state})")
    
    return len(errors) == 0, errors


def verify_port_mappings(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify services have correct port mappings and ports are accessible."""
    errors = []
    
    # Check frontend port (8080)
    if not port_accessible(8080):
        errors.append("Port 8080 (frontend) is not accessible")
    
    # Check backend port (5000)
    if not port_accessible(5000):
        errors.append("Port 5000 (backend) is not accessible")
    
    return len(errors) == 0, errors


def verify_frontend_endpoint(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify frontend is serving the expected content."""
    errors = []
    
    url, expected_status, expected_content = Lab09Config.ENDPOINTS["frontend"]
    
    status, body = http_request(url)
    
    if status == -1:
        errors.append(f"Frontend request failed: {body}")
        return False, errors
    
    if status != expected_status:
        errors.append(f"Frontend returned status {status}, expected {expected_status}")
    
    if expected_content.lower() not in body.lower():
        errors.append(f"Frontend response missing expected content: '{expected_content}'")
    
    return len(errors) == 0, errors


def verify_backend_health(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify backend health endpoint responds correctly."""
    errors = []
    
    url, expected_status, expected_content = Lab09Config.ENDPOINTS["backend_health"]
    
    # Backend might need a moment to start
    max_retries = 3
    for attempt in range(max_retries):
        status, body = http_request(url)
        
        if status == expected_status:
            break
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    if status == -1:
        errors.append(f"Backend health check failed: {body}")
        errors.append("  → Backend might still be starting, or crashed on startup")
        return False, errors
    
    if status != expected_status:
        errors.append(f"Backend /health returned status {status}, expected {expected_status}")
    
    if expected_content.lower() not in body.lower():
        errors.append(f"Backend /health response missing: '{expected_content}'")
    
    return len(errors) == 0, errors


def verify_backend_database_connection(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify backend can query the database and return data."""
    errors = []
    
    url, expected_status, expected_content = Lab09Config.ENDPOINTS["backend_api"]
    
    # Give database time to initialize
    max_retries = 5
    for attempt in range(max_retries):
        status, body = http_request(url, timeout=10)
        
        if status == expected_status and expected_content in body:
            break
        
        if attempt < max_retries - 1:
            time.sleep(3)
    
    if status == -1:
        errors.append(f"Backend API request failed: {body}")
        errors.append("  → Check if database is initialized correctly")
        errors.append("  → Check backend logs: docker compose logs backend")
        return False, errors
    
    if status != expected_status:
        errors.append(f"Backend /submissions returned status {status}, expected {expected_status}")
        if status == 500:
            errors.append("  → 500 error usually means database connection failed")
            errors.append("  → Verify DB_HOST=db in backend environment")
    
    if expected_content not in body:
        errors.append(f"Backend /submissions missing expected data: '{expected_content}'")
        errors.append("  → Database might not be initialized with init.sql")
    
    # Verify response structure
    try:
        data = json.loads(body)
        if isinstance(data, list) and len(data) >= 3:
            # Check for expected students
            names = [item.get("name", "") for item in data]
            expected_names = ["Alice", "Bob", "Charlie"]
            for name in expected_names:
                if name not in names:
                    errors.append(f"Missing expected student: {name}")
        else:
            errors.append("Response should be a list with at least 3 submissions")
    except json.JSONDecodeError:
        errors.append("Backend /submissions did not return valid JSON")
    
    return len(errors) == 0, errors


def verify_volume_exists(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify the database volume exists."""
    errors = []
    
    # Get project name for volume naming
    project_name = get_compose_project_name(exercise_path)
    
    # Possible volume names (docker compose adds project prefix)
    possible_names = [
        "db-data",
        f"{project_name}_db-data",
        f"{project_name}-db-data",
        "lab-09_db-data",
        "lab09_db-data",
    ]
    
    # List all volumes
    code, out, _ = run_cmd(["docker", "volume", "ls", "--format", "{{.Name}}"])
    
    if code != 0:
        return False, ["Could not list volumes"]
    
    existing_volumes = out.split("\n")
    
    found = False
    for vol_name in possible_names:
        if vol_name in existing_volumes:
            found = True
            break
    
    # Also check for any volume containing "db" and "data"
    if not found:
        for vol in existing_volumes:
            if "db" in vol.lower() and "data" in vol.lower():
                found = True
                break
    
    if not found:
        errors.append("Database volume 'db-data' not found")
        errors.append("  → Add 'volumes:' section to docker-compose.yml")
        errors.append("  → Mount volume to db service: db-data:/var/lib/postgresql/data")
    
    return len(errors) == 0, errors


def verify_init_sql_mounted(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify init.sql is properly mounted and executed."""
    errors = []
    
    # Get the db container name
    container_name = get_service_container_name(exercise_path, "db")
    
    if not container_name:
        return False, ["Could not find db container"]
    
    # Check if init.sql exists in the container's init directory
    code, out, _ = run_cmd([
        "docker", "exec", container_name,
        "ls", "/docker-entrypoint-initdb.d/"
    ])
    
    if code != 0:
        errors.append("Could not check init.sql mount")
    elif "init.sql" not in out:
        errors.append("init.sql not found in /docker-entrypoint-initdb.d/")
        errors.append("  → Add bind mount: ./database/init.sql:/docker-entrypoint-initdb.d/init.sql")
    
    # Verify table exists by querying
    code, out, _ = run_cmd([
        "docker", "exec", container_name,
        "psql", "-U", "postgres", "-d", "grademe", 
        "-c", "SELECT COUNT(*) FROM submissions;"
    ])
    
    if code != 0:
        errors.append("Could not query submissions table")
        errors.append("  → init.sql might not have been executed")
        errors.append("  → Try: docker compose down -v && docker compose up -d")
    elif "3" not in out:
        errors.append("submissions table doesn't have expected data (3 rows)")
    
    return len(errors) == 0, errors


def verify_network_communication(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify containers can communicate via service names."""
    errors = []
    
    # Get backend container name
    backend_container = get_service_container_name(exercise_path, "backend")
    
    if not backend_container:
        return False, ["Could not find backend container"]
    
    # Try to ping db from backend
    code, _, _ = run_cmd([
        "docker", "exec", backend_container,
        "ping", "-c", "1", "-W", "2", "db"
    ])
    
    # ping might not be available, try alternative
    if code != 0:
        # Try using Python to test connectivity
        code, out, _ = run_cmd([
            "docker", "exec", backend_container,
            "python", "-c", 
            "import socket; socket.create_connection(('db', 5432), timeout=5); print('OK')"
        ])
        
        if code != 0 or "OK" not in out:
            errors.append("Backend cannot connect to 'db' service")
            errors.append("  → Services should be on the same network")
            errors.append("  → Compose creates this automatically")
    
    return len(errors) == 0, errors


def verify_services_stopped(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify all services have been stopped (for cleanup verification)."""
    success, services, _ = compose_ps(exercise_path)
    
    if not success:
        # If compose ps fails, services might be down
        return True, []
    
    running = [
        s.get("Service") or s.get("service") 
        for s in services 
        if (s.get("State") or s.get("state", "")).lower() in ["running", "up"]
    ]
    
    if running:
        return False, [f"Services still running: {', '.join(running)}"]
    
    return True, []


# ============================================================
# SECTION 5: Task Definitions
# ============================================================

class Task:
    """Represents a single gradeable task."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        points: int,
        verify_func,
        depends_on: List[str] = None,
        hint: str = None,
        category: str = None,
    ):
        self.task_id = task_id
        self.name = name
        self.points = points
        self.verify_func = verify_func
        self.depends_on = depends_on or []
        self.hint = hint
        self.category = category
    
    def verify(self, exercise_path: Path) -> Tuple[bool, int, List[str]]:
        """Run verification and return (passed, points_earned, messages)."""
        try:
            passed, errors = self.verify_func(exercise_path)
            
            if passed:
                return True, self.points, [f"✅ {self.name}"]
            else:
                messages = [f"❌ {self.name}"]
                messages.extend([f"   → {e}" for e in errors])
                if self.hint:
                    messages.append(f"   💡 Hint: {self.hint}")
                return False, 0, messages
        
        except Exception as e:
            return False, 0, [f"❌ {self.name}", f"   → Error: {str(e)}"]


# Define all tasks for Lab 09
LAB_09_TASKS = [
    # ─────────────────────────────────────────────────────────
    # Category A: Prerequisites & Files
    # ─────────────────────────────────────────────────────────
    Task(
        task_id="A1_docker",
        name="Docker is available",
        points=5,
        verify_func=lambda _: verify_docker_available(),
        category="Prerequisites",
    ),
    Task(
        task_id="A2_files",
        name="All required files exist",
        points=10,
        verify_func=verify_required_files,
        depends_on=["A1_docker"],
        hint="Check: docker-compose.yml, frontend/*, backend/*, database/init.sql",
        category="Prerequisites",
    ),
    
    # ─────────────────────────────────────────────────────────
    # Category B: Compose File Structure
    # ─────────────────────────────────────────────────────────
    Task(
        task_id="B1_compose_structure",
        name="docker-compose.yml has correct structure",
        points=15,
        verify_func=verify_compose_file_structure,
        depends_on=["A2_files"],
        hint="Need: services (frontend, backend, db), volumes (db-data)",
        category="Compose Structure",
    ),
    Task(
        task_id="B2_compose_valid",
        name="docker-compose.yml passes validation",
        points=10,
        verify_func=verify_compose_valid,
        depends_on=["B1_compose_structure"],
        hint="Run: docker compose config",
        category="Compose Structure",
    ),
    
    # ─────────────────────────────────────────────────────────
    # Category C: Services Running
    # ─────────────────────────────────────────────────────────
    Task(
        task_id="C1_services_running",
        name="All services are running",
        points=15,
        verify_func=verify_services_running,
        depends_on=["B2_compose_valid"],
        hint="Run: docker compose up --build -d",
        category="Deployment",
    ),
    Task(
        task_id="C2_ports",
        name="Port mappings are correct (8080, 5000)",
        points=10,
        verify_func=verify_port_mappings,
        depends_on=["C1_services_running"],
        hint="frontend: 8080:80, backend: 5000:5000",
        category="Deployment",
    ),
    Task(
        task_id="C3_volume",
        name="Database volume exists",
        points=5,
        verify_func=verify_volume_exists,
        depends_on=["C1_services_running"],
        hint="Add volumes section with db-data",
        category="Deployment",
    ),
    
    # ─────────────────────────────────────────────────────────
    # Category D: Service Functionality
    # ─────────────────────────────────────────────────────────
    Task(
        task_id="D1_frontend",
        name="Frontend serves the portal page",
        points=10,
        verify_func=verify_frontend_endpoint,
        depends_on=["C2_ports"],
        hint="curl localhost:8080 should show 'Grade Me'",
        category="Functionality",
    ),
    Task(
        task_id="D2_backend_health",
        name="Backend /health endpoint responds",
        points=5,
        verify_func=verify_backend_health,
        depends_on=["C2_ports"],
        hint="curl localhost:5000/health",
        category="Functionality",
    ),
    Task(
        task_id="D3_init_sql",
        name="Database initialized with init.sql",
        points=5,
        verify_func=verify_init_sql_mounted,
        depends_on=["C1_services_running"],
        hint="Mount ./database/init.sql to /docker-entrypoint-initdb.d/init.sql",
        category="Functionality",
    ),
    
    # ─────────────────────────────────────────────────────────
    # Category E: Full Stack Integration
    # ─────────────────────────────────────────────────────────
    Task(
        task_id="E1_network",
        name="Containers can communicate by service name",
        points=5,
        verify_func=verify_network_communication,
        depends_on=["C1_services_running"],
        hint="Compose auto-creates network; backend should reach 'db'",
        category="Integration",
    ),
    Task(
        task_id="E2_full_stack",
        name="Backend queries database successfully",
        points=15,
        verify_func=verify_backend_database_connection,
        depends_on=["D2_backend_health", "D3_init_sql", "E1_network"],
        hint="curl localhost:5000/submissions should return Alice, Bob, Charlie",
        category="Integration",
    ),
]


# ============================================================
# SECTION 6: Main Grader
# ============================================================

def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Main grading function for Lab 09: The Full Stack.
    
    Verifies:
    1. All required files exist
    2. docker-compose.yml is valid and correctly structured
    3. All services are running
    4. Frontend, backend, and database are functional
    5. Full stack integration works (backend → database)
    """
    results = []
    total_score = 0
    max_score = sum(t.points for t in LAB_09_TASKS)
    completed_tasks = set()
    
    # Group tasks by category for display
    categories = {}
    
    for task in LAB_09_TASKS:
        # Check dependencies
        deps_met = all(d in completed_tasks for d in task.depends_on)
        
        if not deps_met:
            passed = False
            points = 0
            messages = [f"⏭️  {task.name} (skipped - dependencies not met)"]
        else:
            passed, points, messages = task.verify(exercise_path)
            
            if passed:
                completed_tasks.add(task.task_id)
        
        total_score += points
        
        # Group by category
        cat = task.category or "Other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "task": task,
            "passed": passed,
            "points": points,
            "messages": messages,
        })
    
    # ─────────────────────────────────────────────────────────
    # Build Report
    # ─────────────────────────────────────────────────────────
    lines = []
    
    # Header
    lines.append("╔" + "═"*60 + "╗")
    lines.append("║" + "  Lab 09: The Full Stack - Multi-Service Application  ".center(60) + "║")
    lines.append("╚" + "═"*60 + "╝")
    lines.append("")
    
    # Results by category
    for category, tasks in categories.items():
        cat_passed = sum(1 for t in tasks if t["passed"])
        cat_total = len(tasks)
        cat_points = sum(t["points"] for t in tasks)
        cat_max = sum(t["task"].points for t in tasks)
        
        status_icon = "✅" if cat_passed == cat_total else "🔸" if cat_passed > 0 else "❌"
        lines.append(f"{status_icon} {category} ({cat_passed}/{cat_total} tasks, {cat_points}/{cat_max} pts)")
        lines.append("─" * 60)
        
        for result in tasks:
            for msg in result["messages"]:
                lines.append(f"   {msg}")
        
        lines.append("")
    
    # Score summary
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    passing_score = (max_score * Lab09Config.PASSING_PERCENTAGE) // 100
    
    lines.append("═" * 62)
    lines.append(f"📊 Total Score: {total_score}/{max_score} ({percentage:.0f}%)")
    lines.append(f"   Passing threshold: {Lab09Config.PASSING_PERCENTAGE}% ({passing_score} pts)")
    lines.append("")
    
    passed = total_score >= passing_score
    
    if passed:
        lines.append("🎉 Lab 09 Complete!")
        lines.append("")
        lines.append("Skills Mastered:")
        lines.append("   ✓ Writing multi-service docker-compose.yml")
        lines.append("   ✓ Building custom images in Compose")
        lines.append("   ✓ Configuring service dependencies")
        lines.append("   ✓ Setting up database with init scripts")
        lines.append("   ✓ Inter-service communication")
        lines.append("   ✓ Full stack deployment")
        lines.append("")
        lines.append("➡️  Proceed to Lab 10: Ship It! (Production Patterns)")
    else:
        lines.append("⚠️  Lab 09 not yet complete.")
        lines.append("")
        
        # Provide specific guidance based on what failed
        if "A1_docker" not in completed_tasks:
            lines.append("🔧 First: Ensure Docker is running")
        elif "A2_files" not in completed_tasks:
            lines.append("🔧 First: Create all required files")
        elif "B1_compose_structure" not in completed_tasks:
            lines.append("🔧 Fix: docker-compose.yml structure")
            lines.append("   Need: frontend, backend, db services")
        elif "C1_services_running" not in completed_tasks:
            lines.append("🔧 Run: docker compose up --build -d")
        elif "E2_full_stack" not in completed_tasks:
            lines.append("🔧 Debug: Check logs with 'docker compose logs'")
            lines.append("   Common issues:")
            lines.append("   - DB_HOST should be 'db' (service name)")
            lines.append("   - init.sql must be mounted correctly")
            lines.append("   - Database needs time to initialize")
    
    return passed, "\n".join(lines)


# ============================================================
# SECTION 7: Checkpoint Graders
# ============================================================

def grade_checkpoint_compose(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Checkpoint: Verify only the docker-compose.yml structure.
    Use this before running 'docker compose up'.
    """
    lines = []
    lines.append("╔" + "═"*50 + "╗")
    lines.append("║" + "  Checkpoint: Compose File Validation  ".center(50) + "║")
    lines.append("╚" + "═"*50 + "╝")
    lines.append("")
    
    # Check files
    files_ok, file_errors = verify_required_files(exercise_path)
    if files_ok:
        lines.append("✅ All required files exist")
    else:
        lines.append("❌ Missing files:")
        for err in file_errors:
            lines.append(f"   → {err}")
        return False, "\n".join(lines)
    
    # Check structure
    struct_ok, struct_errors = verify_compose_file_structure(exercise_path)
    if struct_ok:
        lines.append("✅ docker-compose.yml structure is correct")
    else:
        lines.append("❌ Structure issues:")
        for err in struct_errors:
            lines.append(f"   → {err}")
    
    # Check validation
    valid_ok, valid_errors = verify_compose_valid(exercise_path)
    if valid_ok:
        lines.append("✅ docker-compose.yml passes validation")
    else:
        lines.append("❌ Validation failed:")
        for err in valid_errors:
            lines.append(f"   → {err}")
    
    lines.append("")
    
    if struct_ok and valid_ok:
        lines.append("─" * 52)
        lines.append("🎉 Compose file ready!")
        lines.append("   → Run: docker compose up --build -d")
        lines.append("   → Then run the full grader")
        return True, "\n".join(lines)
    
    lines.append("─" * 52)
    lines.append("⚠️  Fix the issues above before proceeding")
    return False, "\n".join(lines)


def grade_checkpoint_services(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Checkpoint: Verify services are running.
    Use this after 'docker compose up'.
    """
    lines = []
    lines.append("╔" + "═"*50 + "╗")
    lines.append("║" + "  Checkpoint: Services Running  ".center(50) + "║")
    lines.append("╚" + "═"*50 + "╝")
    lines.append("")
    
    # Check services
    running_ok, running_errors = verify_services_running(exercise_path)
    if running_ok:
        lines.append("✅ All services running")
    else:
        lines.append("❌ Service issues:")
        for err in running_errors:
            lines.append(f"   → {err}")
        lines.append("")
        lines.append("💡 Debug commands:")
        lines.append("   docker compose ps")
        lines.append("   docker compose logs")
        return False, "\n".join(lines)
    
    # Check ports
    ports_ok, port_errors = verify_port_mappings(exercise_path)
    if ports_ok:
        lines.append("✅ Ports accessible (8080, 5000)")
    else:
        lines.append("❌ Port issues:")
        for err in port_errors:
            lines.append(f"   → {err}")
    
    # Check volume
    vol_ok, vol_errors = verify_volume_exists(exercise_path)
    if vol_ok:
        lines.append("✅ Database volume exists")
    else:
        lines.append("⚠️  Volume issues:")
        for err in vol_errors:
            lines.append(f"   → {err}")
    
    lines.append("")
    
    if running_ok and ports_ok:
        lines.append("─" * 52)
        lines.append("🎉 Services deployed!")
        lines.append("   → Run the full grader to test functionality")
        return True, "\n".join(lines)
    
    return False, "\n".join(lines)


# ============================================================
# SECTION 8: Smart Grader (Auto-detect state)
# ============================================================

def grade_smart(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Smart grading that detects current state and provides appropriate feedback.
    """
    # Check Docker
    docker_ok, _ = docker_available()
    if not docker_ok:
        return False, (
            "╔════════════════════════════════════════════════════════╗\n"
            "║         ❌ Docker is not available                     ║\n"
            "╚════════════════════════════════════════════════════════╝\n\n"
            "Please ensure Docker Desktop is running."
        )
    
    # Check if compose file exists
    compose_file = exercise_path / "docker-compose.yml"
    if not compose_file.exists():
        return False, (
            "╔════════════════════════════════════════════════════════╗\n"
            "║         📍 Lab Status: NOT STARTED                     ║\n"
            "╚════════════════════════════════════════════════════════╝\n\n"
            "docker-compose.yml not found.\n\n"
            "To begin Lab 09:\n"
            "  1. Create docker-compose.yml with three services:\n"
            "     - frontend (build: ./frontend, ports: 8080:80)\n"
            "     - backend (build: ./backend, ports: 5000:5000)\n"
            "     - db (image: postgres:15-alpine)\n"
            "  2. Run: docker compose up --build -d\n"
            "  3. Run this grader again"
        )
    
    # Check if compose is valid
    valid, _, error = compose_config(exercise_path)
    if not valid:
        return grade_checkpoint_compose(grader, code, exercise_path)
    
    # Check if services are running
    success, services, _ = compose_ps(exercise_path)
    running_count = 0
    if success:
        running_count = sum(
            1 for s in services 
            if (s.get("State") or s.get("state", "")).lower() in ["running", "up"]
        )
    
    if running_count == 0:
        return False, (
            "╔════════════════════════════════════════════════════════╗\n"
            "║     📍 Lab Status: COMPOSE READY, NOT RUNNING          ║\n"
            "╚════════════════════════════════════════════════════════╝\n\n"
            "docker-compose.yml exists but services are not running.\n\n"
            "Next step:\n"
            "  docker compose up --build -d\n\n"
            "Then run this grader again."
        )
    
    if running_count < 3:
        return grade_checkpoint_services(grader, code, exercise_path)
    
    # All services running - run full grade
    return grade(grader, code, exercise_path)