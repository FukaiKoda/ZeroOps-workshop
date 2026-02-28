"""
Lab 09 Grader: Ship It!
Production-Ready Practices Validation

Validates:
- Environment file (.env) configuration
- Health checks for services
- Service dependency with health conditions
- Restart policies
- Resource limits
- Actual health status of running services
- Restart policy behavior (container recovery)
"""

from pathlib import Path
from typing import Tuple, List, Optional
import subprocess
import json
import yaml
import re
import time


class Lab09Config:
    """Lab 09 specific configuration."""

    LAB_NUMBER = "09"
    LAB_TITLE = "Ship It! (Production-Ready Practices)"

    REQUIRED_ENV_VARS = [
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "DB_HOST",
    ]

    OPTIONAL_ENV_VARS = [
        "BACKEND_PORT",
        "FRONTEND_PORT",
    ]

    HEALTHCHECK_SERVICES = ["db", "backend"]

    RESTART_SERVICES = ["frontend", "backend", "db"]

    VALID_RESTART_POLICIES = ["always", "unless-stopped", "on-failure"]

    RESOURCE_LIMIT_SERVICES = ["backend"]

    PASSING_PERCENTAGE = 80


def _rendu_dir(exercise_path: Path) -> Path:
    """Get the user's submission directory."""
    return Path.home() / "rendudevops" / exercise_path.name


DEFAULT_FRONTEND_DOCKERFILE = """FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
"""

DEFAULT_FRONTEND_INDEX_HTML = """<!DOCTYPE html>
<html>
<head><title>Grade Me Portal</title></head>
<body>
    <h1>🎓 Grade Me Student Portal</h1>
    <p>API Endpoint: <a href="http://localhost:5000/health">Backend Health</a></p>
</body>
</html>
"""

DEFAULT_BACKEND_DOCKERFILE = """FROM python:3.11-alpine
WORKDIR /app
RUN apk add --no-cache curl
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
"""

DEFAULT_BACKEND_REQUIREMENTS = """flask==3.0.0
psycopg2-binary==2.9.9
"""

DEFAULT_BACKEND_APP_PY = """from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'grademe'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'secretpass')
    )

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "backend"})

@app.route('/submissions')
def submissions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT student_name, grade FROM submissions;')
    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"name": r[0], "grade": r[1]} for r in results])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""

DEFAULT_DATABASE_INIT_SQL = """CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100),
    grade INTEGER
);

INSERT INTO submissions (student_name, grade) VALUES
    ('Alice', 95),
    ('Bob', 87),
    ('Charlie', 92);
"""


def _ensure_project_structure(rendu_path: Path) -> None:
    """Auto-create the entire project structure if it doesn't exist."""
    files_to_create = {
        "frontend/Dockerfile": DEFAULT_FRONTEND_DOCKERFILE,
        "frontend/index.html": DEFAULT_FRONTEND_INDEX_HTML,
        "backend/Dockerfile": DEFAULT_BACKEND_DOCKERFILE,
        "backend/requirements.txt": DEFAULT_BACKEND_REQUIREMENTS,
        "backend/app.py": DEFAULT_BACKEND_APP_PY,
        "database/init.sql": DEFAULT_DATABASE_INIT_SQL,
    }

    try:
        rendu_path.mkdir(parents=True, exist_ok=True)
        for file_path, content in files_to_create.items():
            full_path = rendu_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not full_path.exists():
                full_path.write_text(content)
    except Exception:
        pass


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
    """Make HTTP request and return (status_code, body)."""
    try:
        code, out, err = run_cmd(
            [
                "curl",
                "-s",
                "-o",
                "-",
                "-w",
                "\n%{http_code}",
                "--max-time",
                str(timeout),
                url,
            ]
        )

        if code != 0:
            return -1, err or "Request failed"

        lines = out.rsplit("\n", 1)
        if len(lines) == 2:
            body, status = lines
            return int(status), body
        return -1, "Unexpected response format"
    except Exception as e:
        return -1, str(e)


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

    code, out, err = run_cmd(["docker", "compose", "-f", str(compose_file), "config"])

    if code != 0:
        return False, {}, f"Compose validation failed: {err}"

    try:
        config = yaml.safe_load(out)
        return True, config, ""
    except yaml.YAMLError as e:
        return False, {}, f"Failed to parse compose config: {e}"


def compose_config_raw(exercise_path: Path) -> Tuple[bool, str, str]:
    """
    Get raw docker-compose.yml content (without interpolation).
    Returns (exists, content, error).
    """
    compose_file = exercise_path / "docker-compose.yml"

    if not compose_file.exists():
        return False, "", "docker-compose.yml not found"

    try:
        content = compose_file.read_text()
        return True, content, ""
    except Exception as e:
        return False, "", str(e)


def compose_ps(exercise_path: Path) -> Tuple[bool, List[dict], str]:
    """Get running services status."""
    compose_file = exercise_path / "docker-compose.yml"

    code, out, err = run_cmd(
        ["docker", "compose", "-f", str(compose_file), "ps", "--format", "json"]
    )

    if code != 0:
        return False, [], err

    try:
        services = []
        for line in out.strip().split("\n"):
            if line.strip():
                services.append(json.loads(line))
        return True, services, ""
    except json.JSONDecodeError:
        try:
            services = json.loads(out)
            return True, services if isinstance(services, list) else [services], ""
        except Exception:
            return False, [], "Failed to parse compose ps output"


def get_service_container_name(exercise_path: Path, service: str) -> Optional[str]:
    """Get the actual container name for a compose service."""
    success, services, _ = compose_ps(exercise_path)

    if not success:
        return None

    for svc in services:
        svc_name = svc.get("Service") or svc.get("service") or ""
        if svc_name == service:
            return svc.get("Name") or svc.get("name") or svc.get("ID")

    return None


def get_service_health(exercise_path: Path, service: str) -> Optional[str]:
    """Get the health status of a service."""
    success, services, _ = compose_ps(exercise_path)

    if not success:
        return None

    for svc in services:
        svc_name = svc.get("Service") or svc.get("service") or ""
        if svc_name == service:
            health = svc.get("Health") or svc.get("health") or ""

            if not health:
                container_name = svc.get("Name") or svc.get("name")
                if container_name:
                    exists, data = docker_inspect("container", container_name)
                    if exists:
                        health = (
                            data.get("State", {}).get("Health", {}).get("Status", "")
                        )

            return health

    return None


def verify_docker_available() -> Tuple[bool, List[str]]:
    """Verify Docker is available."""
    ok, info = docker_available()
    if not ok:
        return False, [f"Docker not available: {info}"]
    return True, []


def verify_env_file_exists(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify .env file exists."""
    env_file = exercise_path / ".env"

    if not env_file.exists():
        return False, [
            ".env file not found",
            "  → Create .env with environment variables",
            "  → Example: POSTGRES_PASSWORD=secretpass",
        ]

    return True, []


def verify_env_file_content(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify .env file has required variables."""
    errors = []
    env_file = exercise_path / ".env"

    if not env_file.exists():
        return False, [".env file not found"]

    content = env_file.read_text()
    env_vars = {}

    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip()

    for var in Lab09Config.REQUIRED_ENV_VARS:
        if var not in env_vars:
            errors.append(f"Missing required variable: {var}")
        elif not env_vars[var]:
            errors.append(f"Variable {var} is empty")

    if "POSTGRES_PASSWORD" in env_vars:
        password = env_vars["POSTGRES_PASSWORD"]
        weak_passwords = ["password", "123456", "postgres", "admin", "secret"]
        if password.lower() in weak_passwords:
            errors.append("⚠️  Warning: Weak password detected for POSTGRES_PASSWORD")

    return len(errors) == 0, errors


def verify_compose_uses_env_vars(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify docker-compose.yml uses ${VAR} syntax instead of hardcoded values."""
    errors = []

    exists, content, err = compose_config_raw(exercise_path)

    if not exists:
        return False, [err]

    env_var_pattern = r"\$\{[A-Z_]+\}"
    uses_env_vars = bool(re.search(env_var_pattern, content))

    if not uses_env_vars:
        errors.append("docker-compose.yml doesn't use ${VAR} syntax")
        errors.append("  → Replace hardcoded values with environment variables")
        errors.append("  → Example: POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}")

    expected_usages = [
        ("POSTGRES_PASSWORD", r"\$\{POSTGRES_PASSWORD\}"),
        ("POSTGRES_DB", r"\$\{POSTGRES_DB\}"),
    ]

    for var_name, pattern in expected_usages:
        if not re.search(pattern, content):
            alt_pattern = r"\$" + var_name + r"[^A-Z_]"
            if not re.search(alt_pattern, content):
                errors.append(f"Not using ${{{var_name}}} in compose file")

    hardcoded_patterns = [
        (
            r'POSTGRES_PASSWORD:\s*["\']?[a-zA-Z0-9]+["\']?\s*$',
            "Hardcoded POSTGRES_PASSWORD detected",
        ),
        (r'password:\s*["\']?[a-zA-Z0-9]+["\']?\s*$', "Possible hardcoded password"),
    ]

    for pattern, message in hardcoded_patterns:
        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            if (
                "${"
                not in re.search(pattern, content, re.MULTILINE | re.IGNORECASE).group()
            ):
                errors.append(f"⚠️  {message} - use ${{VAR}} syntax instead")

    return len(errors) == 0, errors


def verify_healthcheck_defined(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify health checks are defined for required services."""
    errors = []

    valid, config, err = compose_config(exercise_path)

    if not valid:
        return False, [f"Could not parse compose file: {err}"]

    services = config.get("services", {})

    for service_name in Lab09Config.HEALTHCHECK_SERVICES:
        if service_name not in services:
            errors.append(f"Service '{service_name}' not found in compose file")
            continue

        service = services[service_name]
        healthcheck = service.get("healthcheck")

        if not healthcheck:
            errors.append(f"Service '{service_name}' missing healthcheck")
            if service_name == "db":
                errors.append("  → Add: healthcheck:")
                errors.append('       test: ["CMD-SHELL", "pg_isready -U postgres"]')
                errors.append("       interval: 10s")
            elif service_name == "backend":
                errors.append("  → Add: healthcheck:")
                errors.append(
                    '       test: ["CMD", "curl", "-f", "http://localhost:5000/health"]'
                )
                errors.append("       interval: 30s")
        else:
            test = healthcheck.get("test")
            if not test:
                errors.append(
                    f"Service '{service_name}' healthcheck missing 'test' command"
                )

            interval = healthcheck.get("interval")
            if not interval:
                errors.append(
                    f"Service '{service_name}' healthcheck missing 'interval'"
                )

    return len(errors) == 0, errors


def verify_depends_on_healthy(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify backend uses depends_on with condition: service_healthy."""
    errors = []

    exists, content, err = compose_config_raw(exercise_path)

    if not exists:
        return False, [err]

    has_condition = "condition:" in content and "service_healthy" in content

    if not has_condition:
        errors.append("Missing 'depends_on' with 'condition: service_healthy'")
        errors.append("  → Update backend service:")
        errors.append("       depends_on:")
        errors.append("         db:")
        errors.append("           condition: service_healthy")
        return False, errors

    valid, config, err = compose_config(exercise_path)

    if not valid:
        return False, [f"Could not parse compose file: {err}"]

    services = config.get("services", {})
    backend = services.get("backend", {})
    depends_on = backend.get("depends_on", {})

    if isinstance(depends_on, list):
        errors.append("backend 'depends_on' uses simple list syntax")
        errors.append("  → Change to object syntax with condition:")
        errors.append("       depends_on:")
        errors.append("         db:")
        errors.append("           condition: service_healthy")
    elif isinstance(depends_on, dict):
        db_dep = depends_on.get("db", {})
        if isinstance(db_dep, dict):
            condition = db_dep.get("condition", "")
            if condition != "service_healthy":
                errors.append(
                    f"backend depends_on db condition is '{condition}', expected 'service_healthy'"
                )
        else:
            errors.append("backend depends_on db should use condition syntax")

    return len(errors) == 0, errors


def verify_restart_policies(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify all services have appropriate restart policies."""
    errors = []

    valid, config, err = compose_config(exercise_path)

    if not valid:
        return False, [f"Could not parse compose file: {err}"]

    services = config.get("services", {})

    for service_name in Lab09Config.RESTART_SERVICES:
        if service_name not in services:
            continue

        service = services[service_name]
        restart = service.get("restart", "no")

        deploy = service.get("deploy", {})
        restart_policy = deploy.get("restart_policy", {})
        deploy_condition = restart_policy.get("condition", "")

        if restart not in Lab09Config.VALID_RESTART_POLICIES and not deploy_condition:
            errors.append(f"Service '{service_name}' has restart policy '{restart}'")
            errors.append("  → Add: restart: unless-stopped")

    return len(errors) == 0, errors


def verify_resource_limits(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify services have resource limits defined (memory required, CPU optional)."""
    errors = []
    warnings = []

    valid, config, err = compose_config(exercise_path)

    if not valid:
        return False, [f"Could not parse compose file: {err}"]

    services = config.get("services", {})

    for service_name in Lab09Config.RESOURCE_LIMIT_SERVICES:
        if service_name not in services:
            continue

        service = services[service_name]
        deploy = service.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})

        if not limits:
            errors.append(f"Service '{service_name}' missing resource limits")
            errors.append("  → Add to service:")
            errors.append("       deploy:")
            errors.append("         resources:")
            errors.append("           limits:")
            errors.append("             memory: 256M")
            errors.append("           (cpus is optional)")
        else:
            if "memory" not in limits:
                errors.append(f"Service '{service_name}' missing memory limit")
                errors.append("  → Add: memory: 256M (or similar)")

            if "cpus" not in limits:
                warnings.append(
                    f"Service '{service_name}' has no CPU limit (optional, some systems don't support it)"
                )

    for service_name, service in services.items():
        if service_name in Lab09Config.RESOURCE_LIMIT_SERVICES:
            continue

        deploy = service.get("deploy", {})
        resources = deploy.get("resources", {})

        if not resources.get("limits"):
            warnings.append(
                f"Service '{service_name}' has no resource limits (recommended for production)"
            )

    return len(errors) == 0, errors + warnings


def verify_services_running(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify all services are running."""
    errors = []

    success, services, err = compose_ps(exercise_path)

    if not success:
        return False, [f"Could not check services: {err}"]

    if not services:
        return False, ["No services running. Run 'docker compose up -d'"]

    running_services = {}
    for svc in services:
        name = svc.get("Service") or svc.get("service") or ""
        state = svc.get("State") or svc.get("state") or ""
        running_services[name] = state

    expected = ["frontend", "backend", "db"]
    for service_name in expected:
        if service_name not in running_services:
            errors.append(f"Service '{service_name}' is not running")
        else:
            state = running_services[service_name]
            if state.lower() not in ["running", "up"]:
                errors.append(
                    f"Service '{service_name}' is not running (state: {state})"
                )

    return len(errors) == 0, errors


def verify_services_healthy(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify services with health checks report healthy status."""
    errors = []

    max_wait = 60
    check_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        all_healthy = True
        current_errors = []

        for service_name in Lab09Config.HEALTHCHECK_SERVICES:
            health = get_service_health(exercise_path, service_name)

            if health is None:
                current_errors.append(
                    f"Could not get health status for '{service_name}'"
                )
                all_healthy = False
            elif health.lower() == "healthy":
                pass
            elif health.lower() == "starting":
                all_healthy = False
            elif health.lower() == "unhealthy":
                current_errors.append(f"Service '{service_name}' is unhealthy")
                current_errors.append(
                    f"  → Check logs: docker compose logs {service_name}"
                )
                all_healthy = False
            elif not health:
                current_errors.append(f"Service '{service_name}' has no health status")
                current_errors.append("  → Healthcheck might not be configured")
                all_healthy = False
            else:
                current_errors.append(
                    f"Service '{service_name}' health status: {health}"
                )
                all_healthy = False

        if all_healthy:
            return True, []

        errors = current_errors

        if elapsed < max_wait - check_interval:
            time.sleep(check_interval)
            elapsed += check_interval
        else:
            break

    errors.insert(0, f"Services not healthy after {max_wait} seconds")
    return False, errors


def verify_restart_policy_works(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Test restart policy by killing a container and checking recovery."""
    errors = []

    container_name = get_service_container_name(exercise_path, "backend")

    if not container_name:
        return False, ["Could not find backend container for restart test"]

    exists, data = docker_inspect("container", container_name)
    if not exists:
        return False, ["Backend container not found"]

    restart_policy = (
        data.get("HostConfig", {}).get("RestartPolicy", {}).get("Name", "no")
    )

    if restart_policy not in Lab09Config.VALID_RESTART_POLICIES:
        errors.append(
            f"Backend restart policy is '{restart_policy}', expected one of {Lab09Config.VALID_RESTART_POLICIES}"
        )
        return False, errors

    code, _, err = run_cmd(["docker", "kill", container_name])

    if code != 0:
        return False, [f"Could not kill container for test: {err}"]

    max_wait = 30
    check_interval = 2
    elapsed = 0
    recovered = False

    while elapsed < max_wait:
        time.sleep(check_interval)
        elapsed += check_interval

        exists, data = docker_inspect("container", container_name)

        if exists:
            is_running = data.get("State", {}).get("Running", False)
            if is_running:
                recovered = True
                break

    if not recovered:
        errors.append(f"Backend container did not recover after {max_wait} seconds")
        errors.append("  → Restart policy might not be configured correctly")
        errors.append("  → Check: restart: unless-stopped")
        return False, errors

    time.sleep(5)

    status, _ = http_request("http://localhost:5000/health", timeout=10)

    if status != 200:
        errors.append("Backend recovered but /health endpoint not responding")
        errors.append("  → Container restarted but application might have issues")

    return len(errors) == 0, errors


def verify_env_vars_resolved(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify that environment variables are properly resolved in config."""
    errors = []

    compose_file = exercise_path / "docker-compose.yml"

    code, out, err = run_cmd(["docker", "compose", "-f", str(compose_file), "config"])

    if code != 0:
        return False, [f"Could not verify env resolution: {err}"]

    unresolved = re.findall(r"\$\{[A-Z_]+\}", out)

    if unresolved:
        errors.append(f"Unresolved environment variables: {', '.join(set(unresolved))}")
        errors.append("  → Check that .env file contains these variables")
        errors.append("  → Verify .env is in the same directory as docker-compose.yml")

    try:
        config = yaml.safe_load(out)
        services = config.get("services", {})

        db_service = services.get("db", {})
        db_env = db_service.get("environment", {})

        if isinstance(db_env, list):
            db_env = dict(e.split("=", 1) if "=" in e else (e, "") for e in db_env)

        postgres_pass = db_env.get("POSTGRES_PASSWORD", "")
        if not postgres_pass or postgres_pass == "${POSTGRES_PASSWORD}":
            errors.append("POSTGRES_PASSWORD not resolved or empty")

    except Exception as e:
        errors.append(f"Could not verify resolved config: {e}")

    return len(errors) == 0, errors


def verify_full_stack_working(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify the full stack is operational after production hardening."""
    errors = []

    status, body = http_request("http://localhost:8080")
    if status != 200:
        errors.append(f"Frontend not responding (status: {status})")
    elif "grade" not in body.lower():
        errors.append("Frontend response missing expected content")

    status, body = http_request("http://localhost:5000/health")
    if status != 200:
        errors.append(f"Backend /health not responding (status: {status})")
    elif "healthy" not in body.lower():
        errors.append("Backend /health not returning healthy status")

    status, body = http_request("http://localhost:5000/submissions")
    if status != 200:
        errors.append(f"Backend /submissions not responding (status: {status})")
    else:
        try:
            data = json.loads(body)
            if not isinstance(data, list) or len(data) < 3:
                errors.append("Backend /submissions not returning expected data")
        except json.JSONDecodeError:
            errors.append("Backend /submissions not returning valid JSON")

    return len(errors) == 0, errors


def verify_gitignore_env(exercise_path: Path) -> Tuple[bool, List[str]]:
    """Verify .env is listed in .gitignore (security best practice)."""
    warnings = []

    gitignore = exercise_path / ".gitignore"

    if not gitignore.exists():
        warnings.append("⚠️  No .gitignore file found")
        warnings.append("  → Create .gitignore and add .env to it")
        warnings.append("  → Never commit .env files with secrets!")
        return True, warnings

    content = gitignore.read_text()

    if ".env" not in content:
        warnings.append("⚠️  .env not listed in .gitignore")
        warnings.append("  → Add '.env' to .gitignore to prevent committing secrets")

    return True, warnings


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
        skip_on_fail: bool = False,
    ):
        self.task_id = task_id
        self.name = name
        self.points = points
        self.verify_func = verify_func
        self.depends_on = depends_on or []
        self.hint = hint
        self.category = category
        self.skip_on_fail = skip_on_fail

    def verify(self, exercise_path: Path) -> Tuple[bool, int, List[str]]:
        """Run verification and return (passed, points_earned, messages)."""
        try:
            passed, errors = self.verify_func(exercise_path)

            if passed:
                warnings = [e for e in errors if e.startswith("⚠️")]
                if warnings:
                    messages = [f"✅ {self.name}"]
                    messages.extend([f"   {w}" for w in warnings])
                    return True, self.points, messages
                return True, self.points, [f"✅ {self.name}"]
            else:
                messages = [f"❌ {self.name}"]
                messages.extend([f"   → {e}" for e in errors])
                if self.hint:
                    messages.append(f"   💡 Hint: {self.hint}")
                return False, 0, messages

        except Exception as e:
            return False, 0, [f"❌ {self.name}", f"   → Error: {str(e)}"]


LAB_09_TASKS = [
    Task(
        task_id="A1_docker",
        name="Docker is available",
        points=5,
        verify_func=lambda _: verify_docker_available(),
        category="Prerequisites",
    ),
    Task(
        task_id="B1_env_exists",
        name=".env file exists",
        points=10,
        verify_func=verify_env_file_exists,
        depends_on=["A1_docker"],
        hint="Create .env file with POSTGRES_PASSWORD, POSTGRES_DB, DB_HOST",
        category="Environment",
    ),
    Task(
        task_id="B2_env_content",
        name=".env has required variables",
        points=10,
        verify_func=verify_env_file_content,
        depends_on=["B1_env_exists"],
        hint="Required: POSTGRES_PASSWORD, POSTGRES_DB, DB_HOST",
        category="Environment",
    ),
    Task(
        task_id="B3_compose_uses_env",
        name="docker-compose.yml uses ${VAR} syntax",
        points=10,
        verify_func=verify_compose_uses_env_vars,
        depends_on=["B1_env_exists"],
        hint="Replace hardcoded values with ${VARIABLE_NAME}",
        category="Environment",
    ),
    Task(
        task_id="B4_env_resolved",
        name="Environment variables resolve correctly",
        points=5,
        verify_func=verify_env_vars_resolved,
        depends_on=["B2_env_content", "B3_compose_uses_env"],
        hint="Run 'docker compose config' to see resolved values",
        category="Environment",
    ),
    Task(
        task_id="B5_gitignore",
        name=".env protected by .gitignore",
        points=5,
        verify_func=verify_gitignore_env,
        depends_on=["B1_env_exists"],
        hint="Add .env to .gitignore for security",
        category="Environment",
    ),
    Task(
        task_id="C1_healthcheck_defined",
        name="Health checks defined for db and backend",
        points=15,
        verify_func=verify_healthcheck_defined,
        depends_on=["A1_docker"],
        hint="Add healthcheck: section to db and backend services",
        category="Health Checks",
    ),
    Task(
        task_id="C2_depends_healthy",
        name="Backend depends_on db with service_healthy condition",
        points=10,
        verify_func=verify_depends_on_healthy,
        depends_on=["C1_healthcheck_defined"],
        hint="Use depends_on: db: condition: service_healthy",
        category="Health Checks",
    ),
    Task(
        task_id="D1_restart_policies",
        name="Restart policies configured for all services",
        points=10,
        verify_func=verify_restart_policies,
        depends_on=["A1_docker"],
        hint="Add 'restart: unless-stopped' to all services",
        category="Restart Policies",
    ),
    Task(
        task_id="E1_resource_limits",
        name="Resource limits configured for backend",
        points=10,
        verify_func=verify_resource_limits,
        depends_on=["A1_docker"],
        hint="Add deploy.resources.limits with cpus and memory",
        category="Resource Limits",
    ),
    Task(
        task_id="F1_services_running",
        name="All services are running",
        points=5,
        verify_func=verify_services_running,
        depends_on=["B4_env_resolved", "C1_healthcheck_defined", "D1_restart_policies"],
        hint="Run: docker compose up -d",
        category="Runtime",
    ),
    Task(
        task_id="F2_services_healthy",
        name="Services report healthy status",
        points=15,
        verify_func=verify_services_healthy,
        depends_on=["F1_services_running", "C1_healthcheck_defined"],
        hint="Check: docker compose ps - Health column should show 'healthy'",
        category="Runtime",
    ),
    Task(
        task_id="F3_full_stack",
        name="Full stack operational",
        points=10,
        verify_func=verify_full_stack_working,
        depends_on=["F2_services_healthy"],
        hint="Test: curl localhost:8080, localhost:5000/health, localhost:5000/submissions",
        category="Runtime",
    ),
    Task(
        task_id="F4_restart_test",
        name="Restart policy works (container recovery)",
        points=10,
        verify_func=verify_restart_policy_works,
        depends_on=["F3_full_stack", "D1_restart_policies"],
        hint="Container should auto-restart after being killed",
        category="Runtime",
    ),
]


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Main grading function for Lab 09: Ship It!

    Verifies:
    1. Environment configuration (.env + ${VAR} syntax)
    2. Health checks for critical services
    3. Dependency conditions (service_healthy)
    4. Restart policies
    5. Resource limits
    6. Runtime health and recovery
    """
    rendu_path = _rendu_dir(exercise_path)
    _ensure_project_structure(rendu_path)

    total_score = 0
    max_score = sum(t.points for t in LAB_09_TASKS)
    completed_tasks = set()

    categories = {}

    for task in LAB_09_TASKS:
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

        cat = task.category or "Other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(
            {
                "task": task,
                "passed": passed,
                "points": points,
                "messages": messages,
            }
        )

    lines = []

    lines.append("╔" + "═" * 62 + "╗")
    lines.append(
        "║" + "  Lab 09: Ship It! - Production-Ready Practices  ".center(62) + "║"
    )
    lines.append("╚" + "═" * 62 + "╝")
    lines.append("")

    for category, tasks in categories.items():
        cat_passed = sum(1 for t in tasks if t["passed"])
        cat_total = len(tasks)
        cat_points = sum(t["points"] for t in tasks)
        cat_max = sum(t["task"].points for t in tasks)

        status_icon = (
            "✅" if cat_passed == cat_total else "🔸" if cat_passed > 0 else "❌"
        )
        lines.append(
            f"{status_icon} {category} ({cat_passed}/{cat_total} tasks, {cat_points}/{cat_max} pts)"
        )
        lines.append("─" * 62)

        for result in tasks:
            for msg in result["messages"]:
                lines.append(f"   {msg}")

        lines.append("")

    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    passing_score = (max_score * Lab09Config.PASSING_PERCENTAGE) // 100

    lines.append("═" * 64)
    lines.append(f"📊 Total Score: {total_score}/{max_score} ({percentage:.0f}%)")
    lines.append(
        f"   Passing threshold: {Lab09Config.PASSING_PERCENTAGE}% ({passing_score} pts)"
    )
    lines.append("")

    passed = total_score >= passing_score

    if passed:
        lines.append("🎉 Lab 09 Complete! Workshop Finished!")
        lines.append("")
        lines.append("Production Skills Mastered:")
        lines.append("   ✓ Environment-based configuration (.env files)")
        lines.append("   ✓ Health checks for reliability monitoring")
        lines.append("   ✓ Service dependencies with health conditions")
        lines.append("   ✓ Automatic restart policies for resilience")
        lines.append("   ✓ Resource limits for stability")
        lines.append("   ✓ Full stack deployment hardening")
        lines.append("")
        lines.append("═" * 64)
        lines.append("🏆 Congratulations! You've completed the Docker Workshop!")
        lines.append("")
        lines.append("Next Steps:")
        lines.append("   → Explore Docker Swarm for orchestration")
        lines.append("   → Learn Kubernetes for enterprise deployments")
        lines.append("   → Set up CI/CD pipelines with Docker")
        lines.append("   → Explore multi-stage builds for optimization")
    else:
        lines.append("⚠️  Lab 09 not yet complete.")
        lines.append("")

        if "B1_env_exists" not in completed_tasks:
            lines.append("🔧 First: Create .env file")
            lines.append("   Example content:")
            lines.append("   POSTGRES_PASSWORD=secretpass")
            lines.append("   POSTGRES_DB=grademe")
            lines.append("   DB_HOST=db")
        elif "B3_compose_uses_env" not in completed_tasks:
            lines.append("🔧 Next: Update docker-compose.yml to use ${VAR} syntax")
            lines.append("   Replace: POSTGRES_PASSWORD: secretpass")
            lines.append("   With:    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}")
        elif "C1_healthcheck_defined" not in completed_tasks:
            lines.append("🔧 Next: Add health checks to services")
            lines.append("   See lab instructions for healthcheck syntax")
        elif "F1_services_running" not in completed_tasks:
            lines.append("🔧 Next: Start the services")
            lines.append("   docker compose up -d")
        elif "F2_services_healthy" not in completed_tasks:
            lines.append("🔧 Debug: Services not healthy")
            lines.append("   docker compose ps")
            lines.append("   docker compose logs")

    return passed, "\n".join(lines)


def grade_checkpoint_config(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Checkpoint: Verify only configuration (before starting services).
    """
    lines = []
    lines.append("╔" + "═" * 52 + "╗")
    lines.append("║" + "  Checkpoint: Configuration Validation  ".center(52) + "║")
    lines.append("╚" + "═" * 52 + "╝")
    lines.append("")

    all_passed = True

    env_ok, env_errors = verify_env_file_exists(exercise_path)
    if env_ok:
        lines.append("✅ .env file exists")
        content_ok, content_errors = verify_env_file_content(exercise_path)
        if content_ok:
            lines.append("✅ .env has required variables")
        else:
            lines.append("❌ .env content issues:")
            for err in content_errors:
                lines.append(f"   → {err}")
            all_passed = False
    else:
        lines.append("❌ .env file missing:")
        for err in env_errors:
            lines.append(f"   → {err}")
        all_passed = False

    compose_ok, compose_errors = verify_compose_uses_env_vars(exercise_path)
    if compose_ok:
        lines.append("✅ docker-compose.yml uses ${VAR} syntax")
    else:
        lines.append("❌ Compose env var issues:")
        for err in compose_errors:
            lines.append(f"   → {err}")
        all_passed = False

    health_ok, health_errors = verify_healthcheck_defined(exercise_path)
    if health_ok:
        lines.append("✅ Health checks defined")
    else:
        lines.append("❌ Health check issues:")
        for err in health_errors:
            lines.append(f"   → {err}")
        all_passed = False

    restart_ok, restart_errors = verify_restart_policies(exercise_path)
    if restart_ok:
        lines.append("✅ Restart policies configured")
    else:
        lines.append("❌ Restart policy issues:")
        for err in restart_errors:
            lines.append(f"   → {err}")
        all_passed = False

    resource_ok, resource_errors = verify_resource_limits(exercise_path)
    if resource_ok:
        lines.append("✅ Resource limits configured")
    else:
        lines.append("⚠️  Resource limit issues:")
        for err in resource_errors:
            lines.append(f"   → {err}")

    lines.append("")

    if all_passed:
        lines.append("─" * 54)
        lines.append("🎉 Configuration ready!")
        lines.append("   → Start services: docker compose up -d")
        lines.append("   → Then run full grader")
        return True, "\n".join(lines)

    lines.append("─" * 54)
    lines.append("⚠️  Fix configuration issues before starting services")
    return False, "\n".join(lines)


def grade_checkpoint_runtime(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Checkpoint: Verify runtime status.
    """
    lines = []
    lines.append("╔" + "═" * 52 + "╗")
    lines.append("║" + "  Checkpoint: Runtime Status  ".center(52) + "║")
    lines.append("╚" + "═" * 52 + "╝")
    lines.append("")

    all_passed = True

    running_ok, running_errors = verify_services_running(exercise_path)
    if running_ok:
        lines.append("✅ All services running")
    else:
        lines.append("❌ Service issues:")
        for err in running_errors:
            lines.append(f"   → {err}")
        all_passed = False

    if not running_ok:
        lines.append("")
        lines.append("─" * 54)
        lines.append("⚠️  Start services first: docker compose up -d")
        return False, "\n".join(lines)

    lines.append("")
    lines.append("Checking health status (may take up to 60 seconds)...")
    health_ok, health_errors = verify_services_healthy(exercise_path)
    if health_ok:
        lines.append("✅ All services healthy")
    else:
        lines.append("❌ Health issues:")
        for err in health_errors:
            lines.append(f"   → {err}")
        all_passed = False

    stack_ok, stack_errors = verify_full_stack_working(exercise_path)
    if stack_ok:
        lines.append("✅ All endpoints responding")
    else:
        lines.append("❌ Endpoint issues:")
        for err in stack_errors:
            lines.append(f"   → {err}")
        all_passed = False

    lines.append("")

    if all_passed:
        lines.append("─" * 54)
        lines.append("🎉 Runtime looks good!")
        lines.append("   → Run full grader for final verification")
        return True, "\n".join(lines)

    lines.append("─" * 54)
    lines.append("⚠️  Debug commands:")
    lines.append("   docker compose ps")
    lines.append("   docker compose logs")
    lines.append("   docker compose logs backend")
    return False, "\n".join(lines)


def grade_smart(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Smart grading that detects current state and provides appropriate feedback.
    """
    docker_ok, _ = docker_available()
    if not docker_ok:
        return False, (
            "╔════════════════════════════════════════════════════════════╗\n"
            "║              ❌ Docker is not available                    ║\n"
            "╚════════════════════════════════════════════════════════════╝\n\n"
            "Please ensure Docker Desktop is running."
        )

    compose_file = exercise_path / "docker-compose.yml"
    env_file = exercise_path / ".env"

    if not compose_file.exists():
        return False, (
            "╔════════════════════════════════════════════════════════════╗\n"
            "║           📍 Lab Status: FILES MISSING                     ║\n"
            "╚════════════════════════════════════════════════════════════╝\n\n"
            "docker-compose.yml not found.\n\n"
            "Lab 09 builds on Lab 09. Make sure you have:\n"
            "  - docker-compose.yml (from Lab 09)\n"
            "  - frontend/, backend/, database/ directories\n\n"
            "Then add production features:\n"
            "  1. Create .env file\n"
            "  2. Update compose to use ${VAR} syntax\n"
            "  3. Add health checks\n"
            "  4. Add restart policies\n"
            "  5. Add resource limits"
        )

    if not env_file.exists():
        return False, (
            "╔════════════════════════════════════════════════════════════╗\n"
            "║      📍 Lab Status: ENVIRONMENT FILE MISSING               ║\n"
            "╚════════════════════════════════════════════════════════════╝\n\n"
            "docker-compose.yml found, but .env file is missing.\n\n"
            "Create .env file with:\n"
            "  POSTGRES_PASSWORD=your_secure_password\n"
            "  POSTGRES_DB=grademe\n"
            "  DB_HOST=db\n"
            "  BACKEND_PORT=5000\n"
            "  FRONTEND_PORT=8080\n\n"
            "Then run the grader again."
        )

    health_ok, _ = verify_healthcheck_defined(exercise_path)
    restart_ok, _ = verify_restart_policies(exercise_path)

    if not health_ok or not restart_ok:
        return grade_checkpoint_config(code, exercise_path)

    success, services, _ = compose_ps(exercise_path)
    running_count = 0
    if success:
        running_count = sum(
            1
            for s in services
            if (s.get("State") or s.get("state", "")).lower() in ["running", "up"]
        )

    if running_count == 0:
        return False, (
            "╔════════════════════════════════════════════════════════════╗\n"
            "║     📍 Lab Status: CONFIGURED, NOT RUNNING                 ║\n"
            "╚════════════════════════════════════════════════════════════╝\n\n"
            "Configuration looks good! Services are not running.\n\n"
            "Next step:\n"
            "  docker compose up -d\n\n"
            "Then run this grader again."
        )

    if running_count < 3:
        return grade_checkpoint_runtime(code, exercise_path)

    return grade(code, exercise_path)
