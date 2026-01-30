"""
Docker Runner: Low-level Docker SDK wrapper for executing grading containers.

Responsibilities:
- Spawn containers from pre-built images (python-runner, c-runner)
- Mount student code safely
- Enforce security (no network, resource limits)
- Enforce timeouts (kill if running > N seconds)
- Capture output and return exit code
"""

import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
import docker
from docker.types import Mount
import subprocess

logger = logging.getLogger(__name__)


class DockerRunnerException(Exception):
    """Base exception for Docker runner errors."""
    pass


class DockerRunner:
    """
    Thin wrapper around docker.client.DockerClient.
    
    Usage:
        runner = DockerRunner()
        output, exit_code = runner.run_container(
            image="python-runner:latest",
            command=["python", "/student/test.py"],
            mount_source="/tmp/student_code",
            mount_target="/student",
            timeout_seconds=10
        )
    """

    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            self.client.ping()  # Verify Docker daemon is reachable
            logger.info("✅ Docker daemon connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Docker daemon: {e}")
            raise DockerRunnerException(f"Docker connection failed: {e}")

    def run_container(
        self,
        image: str,
        command: list,
        mount_source: str,
        mount_target: str = "/student",
        timeout_seconds: int = 10,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, int]:
        """
        Run a container with student code mounted.

        Args:
            image: Docker image name (e.g., "python-runner:latest")
            command: Command to execute (e.g., ["python", "/student/test.py"])
            mount_source: Host directory with student code
            mount_target: Where to mount inside container
            timeout_seconds: Kill container if it runs longer
            env_vars: Environment variables to pass to container

        Returns:
            (output, exit_code): stdout+stderr, and container exit code

        Raises:
            DockerRunnerException: If container fails to start or times out
        """
        logger.info(f"🚀 Starting container: {image}")
        logger.info(f"   Mount: {mount_source} -> {mount_target}")
        logger.info(f"   Timeout: {timeout_seconds}s")

        try:
            # Pull image if not already present
            try:
                self.client.images.get(image)
            except docker.errors.ImageNotFound:
                logger.info(f"📥 Pulling image: {image}")
                self.client.images.pull(image)

            # Prepare mounts
            mounts = [
                Mount(
                    target=mount_target,
                    source=mount_source,
                    type="bind",
                    read_only=False,
                )
            ]

            # Prepare environment
            environment = env_vars or {}

            # Run container with security restrictions
            container = self.client.containers.run(
                image=image,
                command=command,
                mounts=mounts,
                environment=environment,
                network_mode="none",  # ❌ No network access
                mem_limit="256m",  # 256 MB RAM limit
                memswap_limit="256m",  # No swap
                cpus=1.0,  # 1 CPU max
                detach=True,  # Run in background
                stdout=True,
                stderr=True,
                user="1000:1000",  # Run as non-root if possible
            )

            logger.info(f"   Container ID: {container.id[:12]}")

            # Wait for container to finish (with timeout)
            try:
                exit_code = container.wait(timeout=timeout_seconds)["StatusCode"]
                output = container.logs(stdout=True, stderr=True).decode("utf-8")
                logger.info(f"✅ Container finished with exit code: {exit_code}")
                return output, exit_code

            except docker.errors.APIError as e:
                # Timeout or other API error
                logger.warning(f"⏱️ Timeout or error, killing container: {e}")
                container.kill()
                raise DockerRunnerException(f"Container timeout or error: {e}")

        except docker.errors.ImageNotFound as e:
            logger.error(f"❌ Image not found: {image}")
            raise DockerRunnerException(f"Image not found: {image}")
        except docker.errors.APIError as e:
            logger.error(f"❌ Docker API error: {e}")
            raise DockerRunnerException(f"Docker API error: {e}")
        finally:
            # Cleanup: Remove container after execution
            try:
                container.remove(force=True)
                logger.debug(f"   Cleaned up container: {container.id[:12]}")
            except:
                pass

    def execute_grading(
        self,
        docker_image: str,
        student_code_dir: str,
        grader_script: str,
        timeout_seconds: int = 10,
    ) -> Tuple[str, int]:
        """
        High-level method: Execute a grading script against student code.

        Assumes:
        - Student code is in student_code_dir (host)
        - Grader script is in the container at /grader/test.py
        - We need to run: python /grader/test.py

        Args:
            docker_image: e.g., "python-runner:latest"
            student_code_dir: Path to student code on host
            grader_script: The grader script name (e.g., "test.py")
            timeout_seconds: Kill if running too long

        Returns:
            (output, exit_code): stdout+stderr and exit code
        """
        logger.info(f"📋 Executing grading: {grader_script}")

        # Mount student code at /student
        output, exit_code = self.run_container(
            image=docker_image,
            command=["python", f"/grader/{grader_script}"],
            mount_source=student_code_dir,
            mount_target="/student",
            timeout_seconds=timeout_seconds,
        )

        return output, exit_code

    def health_check(self) -> bool:
        """
        Check if Docker daemon is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker health check failed: {e}")
            return False


# ==========================================
# Utility: Create a temporary directory for student code
# ==========================================

def create_temp_student_dir(files: Dict[str, str]) -> str:
    """
    Create a temporary directory and write student files into it.

    Args:
        files: Dict of {filename: content}

    Returns:
        Path to temporary directory
    """
    tmpdir = tempfile.mkdtemp(prefix="student_")
    logger.info(f"📁 Created temp dir: {tmpdir}")

    for filename, content in files.items():
        filepath = Path(tmpdir) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)
        logger.debug(f"   Wrote: {filename}")

    return tmpdir


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    runner = DockerRunner()
    print(f"Health check: {runner.health_check()}")
