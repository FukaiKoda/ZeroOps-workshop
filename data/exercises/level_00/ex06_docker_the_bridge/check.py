"""Interactive Docker validation for Lab 06: The Bridge.

GRADING STRATEGY:
=================
This grader has TWO modes based on the current state:

MODE 1 - "BUILD" (Parts A-C):
    - Network must EXIST
    - Containers must be RUNNING
    - Connectivity must WORK
    - Creates a marker file on success

MODE 2 - "CLEANUP" (Part D):
    - Network must NOT exist
    - Containers must NOT exist
    - Marker file from Mode 1 must EXIST (proves they completed Build phase)

The student must:
1. Complete Parts A-C → Submit → Pass Mode 1
2. Complete Part D (cleanup) → Submit again → Pass Mode 2

Contract:
    grade(grader, code, exercise_path) -> (success: bool, message: str)
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

NETWORK = "grademe-network"
DB_CONTAINER = "grademe-db"
API_CONTAINER = "grademe-api"
DB_ALONE_CONTAINER = "db-alone"
POSTGRES_PASSWORD = "secretpass"

MARKER_FILE_NAME = ".lab06_build_complete"

POINTS_PART_A = 10
POINTS_PART_B = 30
POINTS_PART_C = 30
POINTS_PART_D = 30
TOTAL_POINTS = POINTS_PART_A + POINTS_PART_B + POINTS_PART_C + POINTS_PART_D
PASS_THRESHOLD = 90


class GradingMode(Enum):
    BUILD = "build"
    CLEANUP = "cleanup"


class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class CheckResult:
    """Result of a single validation check."""

    passed: bool
    description: str
    points_earned: int
    points_possible: int
    hint: Optional[str] = None
    details: Optional[str] = None


@dataclass
class PartResult:
    """Result of a complete part (A, B, C, or D)."""

    part_name: str
    status: TaskStatus
    checks: List[CheckResult] = field(default_factory=list)
    total_earned: int = 0
    total_possible: int = 0
    blocking_error: Optional[str] = None

    def add_check(self, check: CheckResult) -> None:
        self.checks.append(check)
        self.total_earned += check.points_earned
        self.total_possible += check.points_possible

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks) if self.checks else False


@dataclass
class GradingReport:
    """Complete grading report for the lab."""

    mode: GradingMode = GradingMode.BUILD
    parts: Dict[str, PartResult] = field(default_factory=dict)
    total_earned: int = 0
    total_possible: int = TOTAL_POINTS
    passed: bool = False
    summary_message: str = ""

    def add_part(self, part: PartResult) -> None:
        self.parts[part.part_name] = part
        self.total_earned += part.total_earned

    def finalize(self, exercise_path: Path) -> None:
        """Calculate final results and generate summary."""
        self.passed = self.total_earned >= PASS_THRESHOLD
        self._build_summary(exercise_path)

    def _build_summary(self, exercise_path: Path) -> None:
        """Build the summary message."""
        lines = []
        lines.append("=" * 60)
        lines.append("🌉 Lab 06: The Bridge - Grading Results")
        lines.append(f"   Mode: {self.mode.value.upper()}")
        lines.append("=" * 60)
        lines.append("")

        for part_name, part in self.parts.items():
            status_icon = {
                TaskStatus.PASSED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.IN_PROGRESS: "⏳",
                TaskStatus.NOT_STARTED: "⬜",
            }.get(part.status, "❓")

            lines.append(
                f"Part {part_name}: {status_icon} ({part.total_earned}/{part.total_possible} pts)"
            )
            lines.append("-" * 40)

            for check in part.checks:
                icon = "✅" if check.passed else "❌"
                lines.append(f"  {icon} {check.description}")
                lines.append(
                    f"      Points: {check.points_earned}/{check.points_possible}"
                )
                if not check.passed and check.hint:
                    lines.append(f"      💡 Hint: {check.hint}")

            if part.blocking_error:
                lines.append(f"  ⚠️  {part.blocking_error}")

            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Total Score: {self.total_earned}/{self.total_possible} points")
        lines.append(f"Pass Threshold: {PASS_THRESHOLD} points")
        lines.append("")

        if self.passed:
            lines.append("🎉 PASSED! Excellent work!")
            lines.append("")
            lines.append("Key Takeaways:")
            lines.append("  • Custom bridge networks provide DNS-based discovery")
            lines.append("  • Containers on the same network communicate by name")
            lines.append("  • Always clean up resources when done")
        else:
            lines.append("📚 Not yet passed. See hints above.")
            lines.append("")
            self._add_mode_specific_guidance(lines, exercise_path)

        lines.append("=" * 60)

        self.summary_message = "\n".join(lines)

    def _add_mode_specific_guidance(
        self, lines: List[str], exercise_path: Path
    ) -> None:
        """Add guidance based on current mode."""
        marker_path = exercise_path / MARKER_FILE_NAME

        if self.mode == GradingMode.BUILD:
            lines.append("📋 You are in BUILD mode (Parts A-C)")
            lines.append("   Complete the following:")
            lines.append(f"   1. Create network: docker network create {NETWORK}")
            lines.append(
                f"   2. Run PostgreSQL: docker run -d --name {DB_CONTAINER} \\"
            )
            lines.append(
                f"        --network {NETWORK} -e POSTGRES_PASSWORD={POSTGRES_PASSWORD} \\"
            )
            lines.append("        postgres:15-alpine")
            lines.append(f"   3. Run Alpine: docker run -d --name {API_CONTAINER} \\")
            lines.append(f"        --network {NETWORK} alpine sleep 3600")
            lines.append(
                f"   4. Install psql: docker exec {API_CONTAINER} apk add --no-cache postgresql-client"
            )
            lines.append("   5. Submit to pass BUILD mode")
        else:
            lines.append("📋 You are in CLEANUP mode (Part D)")
            if not marker_path.exists():
                lines.append("   ⚠️  You must complete BUILD mode first!")
                lines.append(
                    "   Re-create the network and containers, submit to pass BUILD,"
                )
                lines.append("   then clean up and submit again.")
            else:
                lines.append("   Complete the following:")
                lines.append(
                    f"   1. Stop containers: docker stop {DB_CONTAINER} {API_CONTAINER}"
                )
                lines.append(
                    f"   2. Remove containers: docker rm {DB_CONTAINER} {API_CONTAINER}"
                )
                lines.append(f"   3. Remove network: docker network rm {NETWORK}")
                lines.append("   4. Submit to pass CLEANUP mode")


def _run_command(args: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
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
    """Check if Docker is available and running."""
    code, out, err = _run_command(
        ["docker", "info", "--format", "{{.ServerVersion}}"], timeout=5
    )
    if code != 0:
        return False, err or out or "Docker is not available"
    return True, out


def _network_exists(name: str) -> bool:
    """Check if a Docker network exists."""
    code, _, _ = _run_command(["docker", "network", "inspect", name], timeout=10)
    return code == 0


def _get_network_driver(name: str) -> Optional[str]:
    """Get the driver type for a network."""
    code, out, _ = _run_command(
        ["docker", "network", "inspect", name, "--format", "{{.Driver}}"], timeout=10
    )
    return out.strip() if code == 0 else None


def _container_exists(name: str) -> bool:
    """Check if a container exists (running or stopped)."""
    code, out, _ = _run_command(
        ["docker", "ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"],
        timeout=10,
    )
    return code == 0 and bool(out.strip())


def _container_running(name: str) -> bool:
    """Check if a container is running."""
    code, out, _ = _run_command(
        ["docker", "ps", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"],
        timeout=10,
    )
    return code == 0 and bool(out.strip())


def _inspect_container(name: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Inspect a container and return its JSON data."""
    code, out, err = _run_command(["docker", "inspect", name], timeout=10)
    if code != 0:
        return False, None, err or out or "inspect failed"
    try:
        data = json.loads(out)
        if isinstance(data, list) and data:
            return True, data[0], ""
        if isinstance(data, dict):
            return True, data, ""
        return False, None, "Unexpected JSON output"
    except json.JSONDecodeError as e:
        return False, None, f"Failed to parse JSON: {e}"


def _container_on_network(container: str, network: str) -> bool:
    """Check if a container is attached to a specific network."""
    ok, inspected, _ = _inspect_container(container)
    if not ok or not inspected:
        return False
    networks = inspected.get("NetworkSettings", {}).get("Networks", {})
    return network in networks if isinstance(networks, dict) else False


def _container_uses_links(container: str) -> bool:
    """Check if a container uses deprecated --link option."""
    ok, inspected, _ = _inspect_container(container)
    if not ok or not inspected:
        return False
    links = inspected.get("HostConfig", {}).get("Links")
    return links is not None and len(links) > 0


def _get_container_env(container: str) -> List[str]:
    """Get environment variables from a container."""
    ok, inspected, _ = _inspect_container(container)
    if not ok or not inspected:
        return []
    return inspected.get("Config", {}).get("Env", [])


def _ping_from_container(source: str, target: str) -> Tuple[bool, str]:
    """Ping a target from a source container."""
    code, out, err = _run_command(
        ["docker", "exec", source, "ping", "-c", "3", target], timeout=15
    )
    if code != 0:
        return False, err or out or "ping failed"
    return "bytes from" in out.lower(), out


def _psql_client_installed(container: str) -> bool:
    """Check if postgresql-client is installed in a container."""
    code, _, _ = _run_command(
        ["docker", "exec", container, "which", "psql"],
        timeout=10,
    )
    return code == 0


def _test_psql_connection(
    api_container: str, db_container: str, password: str
) -> Tuple[bool, str]:
    """Test PostgreSQL connection from api container to db container."""
    code, out, err = _run_command(
        [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={password}",
            api_container,
            "psql",
            "-h",
            db_container,
            "-U",
            "postgres",
            "-c",
            "\\conninfo",
        ],
        timeout=15,
    )
    if code != 0:
        return False, err or out or "Connection failed"
    return True, out


def _get_marker_path(exercise_path: Path) -> Path:
    """Get the path to the marker file."""
    return exercise_path / MARKER_FILE_NAME


def _marker_exists(exercise_path: Path) -> bool:
    """Check if the build completion marker exists."""
    return _get_marker_path(exercise_path).exists()


def _create_marker(exercise_path: Path) -> None:
    """Create the build completion marker."""
    marker_path = _get_marker_path(exercise_path)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marker_path, "w") as f:
        f.write(f"Lab 06 Build Phase completed at {datetime.now().isoformat()}\n")
        f.write("Do not delete this file until you pass the cleanup phase.\n")


def _remove_marker(exercise_path: Path) -> None:
    """Remove the build completion marker."""
    marker_path = _get_marker_path(exercise_path)
    if marker_path.exists():
        marker_path.unlink()


def _determine_mode(exercise_path: Path) -> GradingMode:
    """
    Determine which grading mode to use based on current state.

    Logic:
    - If network/containers EXIST → BUILD mode (validate they're correct)
    - If network/containers DON'T EXIST and marker EXISTS → CLEANUP mode
    - If nothing exists and no marker → BUILD mode (they need to start)
    """
    network_exists = _network_exists(NETWORK)
    db_exists = _container_exists(DB_CONTAINER)
    api_exists = _container_exists(API_CONTAINER)
    marker_exists = _marker_exists(exercise_path)

    if network_exists or db_exists or api_exists:
        return GradingMode.BUILD

    if marker_exists:
        return GradingMode.CLEANUP

    return GradingMode.BUILD


def validate_build_part_a(exercise_path: Path) -> PartResult:
    """Validate Part A: Cleanup of default network test."""
    result = PartResult(part_name="A", status=TaskStatus.IN_PROGRESS)

    if not _container_exists(DB_ALONE_CONTAINER):
        result.add_check(
            CheckResult(
                passed=True,
                description=f"Container '{DB_ALONE_CONTAINER}' cleaned up",
                points_earned=5,
                points_possible=5,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Container '{DB_ALONE_CONTAINER}' cleaned up",
                points_earned=0,
                points_possible=5,
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = "Clean up Part A test containers first"
        return result

    if _network_exists(NETWORK):
        result.add_check(
            CheckResult(
                passed=True,
                description="Proceeded to Part B (network created)",
                points_earned=5,
                points_possible=5,
            )
        )
        result.status = TaskStatus.PASSED
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description="Proceeded to Part B (network created)",
                points_earned=0,
                points_possible=5,
                hint=f"Create network: docker network create {NETWORK}",
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = "Create the custom network to proceed"

    return result


def validate_build_part_b() -> PartResult:
    """Validate Part B: Custom network and containers."""
    result = PartResult(part_name="B", status=TaskStatus.IN_PROGRESS)

    if _network_exists(NETWORK):
        driver = _get_network_driver(NETWORK)
        if driver == "bridge":
            result.add_check(
                CheckResult(
                    passed=True,
                    description=f"Network '{NETWORK}' exists (bridge driver)",
                    points_earned=6,
                    points_possible=6,
                )
            )
        else:
            result.add_check(
                CheckResult(
                    passed=False,
                    description=f"Network '{NETWORK}' is bridge type",
                    points_earned=0,
                    points_possible=6,
                    hint=f"Driver is '{driver}', expected 'bridge'",
                )
            )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Network '{NETWORK}' exists",
                points_earned=0,
                points_possible=6,
                hint=f"Create it: docker network create {NETWORK}",
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = "Network must exist"
        return result

    if _container_running(DB_CONTAINER):
        if _container_on_network(DB_CONTAINER, NETWORK):
            result.add_check(
                CheckResult(
                    passed=True,
                    description=f"Container '{DB_CONTAINER}' running on '{NETWORK}'",
                    points_earned=8,
                    points_possible=8,
                )
            )
        else:
            result.add_check(
                CheckResult(
                    passed=False,
                    description=f"Container '{DB_CONTAINER}' on '{NETWORK}'",
                    points_earned=0,
                    points_possible=8,
                    hint=f"Recreate with --network={NETWORK}",
                )
            )
            result.status = TaskStatus.FAILED
            return result
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Container '{DB_CONTAINER}' running",
                points_earned=0,
                points_possible=8,
                hint=f"Create: docker run -d --name {DB_CONTAINER} --network {NETWORK} -e POSTGRES_PASSWORD={POSTGRES_PASSWORD} postgres:15-alpine",
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = f"Container '{DB_CONTAINER}' must be running"
        return result

    if _container_running(API_CONTAINER):
        if _container_on_network(API_CONTAINER, NETWORK):
            result.add_check(
                CheckResult(
                    passed=True,
                    description=f"Container '{API_CONTAINER}' running on '{NETWORK}'",
                    points_earned=8,
                    points_possible=8,
                )
            )
        else:
            result.add_check(
                CheckResult(
                    passed=False,
                    description=f"Container '{API_CONTAINER}' on '{NETWORK}'",
                    points_earned=0,
                    points_possible=8,
                    hint=f"Recreate with --network={NETWORK}",
                )
            )
            result.status = TaskStatus.FAILED
            return result
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Container '{API_CONTAINER}' running",
                points_earned=0,
                points_possible=8,
                hint=f"Create: docker run -d --name {API_CONTAINER} --network {NETWORK} alpine sleep 3600",
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = f"Container '{API_CONTAINER}' must be running"
        return result

    ping_ok, _ = _ping_from_container(API_CONTAINER, DB_CONTAINER)
    if ping_ok:
        result.add_check(
            CheckResult(
                passed=True,
                description=f"DNS works: '{API_CONTAINER}' can ping '{DB_CONTAINER}'",
                points_earned=8,
                points_possible=8,
            )
        )
        result.status = TaskStatus.PASSED
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description="DNS resolution (ping by name)",
                points_earned=0,
                points_possible=8,
                hint="Both containers must be on the same custom network",
            )
        )
        result.status = TaskStatus.FAILED

    return result


def validate_build_part_c() -> PartResult:
    """Validate Part C: Real PostgreSQL connectivity."""
    result = PartResult(part_name="C", status=TaskStatus.IN_PROGRESS)

    if _psql_client_installed(API_CONTAINER):
        result.add_check(
            CheckResult(
                passed=True,
                description=f"PostgreSQL client installed in '{API_CONTAINER}'",
                points_earned=10,
                points_possible=10,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"PostgreSQL client installed in '{API_CONTAINER}'",
                points_earned=0,
                points_possible=10,
                hint=f"Install: docker exec {API_CONTAINER} apk add --no-cache postgresql-client",
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = "Install PostgreSQL client to continue"
        return result

    conn_ok, conn_msg = _test_psql_connection(
        API_CONTAINER, DB_CONTAINER, POSTGRES_PASSWORD
    )
    if conn_ok:
        result.add_check(
            CheckResult(
                passed=True,
                description="PostgreSQL connection works",
                points_earned=10,
                points_possible=10,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description="PostgreSQL connection works",
                points_earned=0,
                points_possible=10,
                hint=f"Ensure '{DB_CONTAINER}' has POSTGRES_PASSWORD={POSTGRES_PASSWORD}",
                details=conn_msg,
            )
        )
        result.status = TaskStatus.FAILED
        return result

    env_vars = _get_container_env(DB_CONTAINER)
    password_ok = any(f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}" in e for e in env_vars)
    if password_ok:
        result.add_check(
            CheckResult(
                passed=True,
                description="PostgreSQL password configured correctly",
                points_earned=5,
                points_possible=5,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description="PostgreSQL password configured correctly",
                points_earned=0,
                points_possible=5,
                hint=f"Password must be '{POSTGRES_PASSWORD}'",
            )
        )

    uses_links = _container_uses_links(DB_CONTAINER) or _container_uses_links(
        API_CONTAINER
    )
    if not uses_links:
        result.add_check(
            CheckResult(
                passed=True,
                description="No deprecated --link usage",
                points_earned=5,
                points_possible=5,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description="No deprecated --link usage",
                points_earned=0,
                points_possible=5,
                hint="Use custom networks, not --link",
            )
        )

    result.status = TaskStatus.PASSED if result.all_passed else TaskStatus.FAILED
    return result


def validate_cleanup_part_d(exercise_path: Path) -> PartResult:
    """Validate Part D: Everything cleaned up."""
    result = PartResult(part_name="D", status=TaskStatus.IN_PROGRESS)

    if not _marker_exists(exercise_path):
        result.add_check(
            CheckResult(
                passed=False,
                description="Build phase completed previously",
                points_earned=0,
                points_possible=0,
                hint="You must complete Parts A-C first (submit while containers exist)",
            )
        )
        result.status = TaskStatus.FAILED
        result.blocking_error = "Complete BUILD mode first, then clean up"
        return result
    else:
        result.add_check(
            CheckResult(
                passed=True,
                description="Build phase completed previously",
                points_earned=0,
                points_possible=0,
            )
        )

    if not _container_exists(DB_CONTAINER):
        result.add_check(
            CheckResult(
                passed=True,
                description=f"Container '{DB_CONTAINER}' removed",
                points_earned=10,
                points_possible=10,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Container '{DB_CONTAINER}' removed",
                points_earned=0,
                points_possible=10,
                hint=f"Remove: docker rm -f {DB_CONTAINER}",
            )
        )

    if not _container_exists(API_CONTAINER):
        result.add_check(
            CheckResult(
                passed=True,
                description=f"Container '{API_CONTAINER}' removed",
                points_earned=10,
                points_possible=10,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Container '{API_CONTAINER}' removed",
                points_earned=0,
                points_possible=10,
                hint=f"Remove: docker rm -f {API_CONTAINER}",
            )
        )

    if not _network_exists(NETWORK):
        result.add_check(
            CheckResult(
                passed=True,
                description=f"Network '{NETWORK}' removed",
                points_earned=10,
                points_possible=10,
            )
        )
    else:
        result.add_check(
            CheckResult(
                passed=False,
                description=f"Network '{NETWORK}' removed",
                points_earned=0,
                points_possible=10,
                hint=f"Remove: docker network rm {NETWORK}",
            )
        )

    result.status = TaskStatus.PASSED if result.all_passed else TaskStatus.FAILED
    return result


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Main grading function for Lab 06: The Bridge.

    Two-phase grading:
    - BUILD mode: Validates Parts A, B, C (infrastructure exists)
    - CLEANUP mode: Validates Part D (infrastructure removed)
    """
    if isinstance(exercise_path, str):
        exercise_path = Path(exercise_path)

    docker_ok, docker_info = _docker_available()
    if not docker_ok:
        return False, f"Docker is not available: {docker_info}"

    mode = _determine_mode(exercise_path)
    report = GradingReport(mode=mode)

    if mode == GradingMode.BUILD:

        part_a = validate_build_part_a(exercise_path)
        report.add_part(part_a)

        if part_a.status != TaskStatus.PASSED:
            report.finalize(exercise_path)
            return False, report.summary_message

        part_b = validate_build_part_b()
        report.add_part(part_b)

        if part_b.status != TaskStatus.PASSED:
            report.finalize(exercise_path)
            return False, report.summary_message

        part_c = validate_build_part_c()
        report.add_part(part_c)

        if part_c.status != TaskStatus.PASSED:
            report.finalize(exercise_path)
            return False, report.summary_message

        _create_marker(exercise_path)

        part_d_placeholder = PartResult(part_name="D", status=TaskStatus.NOT_STARTED)
        part_d_placeholder.add_check(
            CheckResult(
                passed=False,
                description="Cleanup (submit again after removing containers/network)",
                points_earned=0,
                points_possible=30,
                hint="Now clean up everything and submit again to complete the lab",
            )
        )
        report.add_part(part_d_placeholder)

        report.finalize(exercise_path)

        build_message = report.summary_message
        build_message += "\n\n" + "=" * 60
        build_message += "\n🔔 BUILD PHASE COMPLETE!"
        build_message += "\n" + "=" * 60
        build_message += "\n\nNow complete Part D"
        build_message += "\n\n⚠️  Lab is NOT complete until cleanup is verified!"

        return False, build_message

    else:

        part_a = PartResult(part_name="A", status=TaskStatus.PASSED)
        part_a.add_check(CheckResult(True, "Previously completed", 10, 10))
        report.add_part(part_a)

        part_b = PartResult(part_name="B", status=TaskStatus.PASSED)
        part_b.add_check(CheckResult(True, "Previously completed", 30, 30))
        report.add_part(part_b)

        part_c = PartResult(part_name="C", status=TaskStatus.PASSED)
        part_c.add_check(CheckResult(True, "Previously completed", 30, 30))
        report.add_part(part_c)

        part_d = validate_cleanup_part_d(exercise_path)
        report.add_part(part_d)

        if part_d.status == TaskStatus.PASSED:
            _remove_marker(exercise_path)

        report.finalize(exercise_path)
        return report.passed, report.summary_message


def main():
    """Run grading as standalone script."""
    import sys

    exercise_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    success, message = grade(None, "", exercise_path)
    print(message)
    print()
    print(f"Result: {'PASSED ✅' if success else 'NOT PASSED ❌'}")
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
