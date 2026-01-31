"""
Grader: High-level grading engine that processes WorkerJob objects.

This is the "execution engine" that:
1. Receives a WorkerJob (user code + exercise metadata)
2. Prepares a temporary directory with student files
3. Mounts it in a Docker container
4. Runs the grading script
5. Parses the output and returns a result

Typically called by a background worker (Celery, RQ, or similar).
"""

import logging
import json
import re
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from workers.docker_runner import DockerRunner, DockerRunnerException, create_temp_student_dir
from workers.sandbox import get_sandbox_config, sandbox_config_to_docker_kwargs

# Import schemas from shared module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
from schemas import WorkerJob, WorkerJobResult, ExerciseStatus

logger = logging.getLogger(__name__)


class GraderException(Exception):
    """Base exception for grader errors."""
    pass


class Grader:
    """
    High-level grading orchestrator.
    
    Usage:
        grader = Grader()
        result = grader.grade_submission(worker_job)
    """

    def __init__(self):
        """Initialize grader with Docker runner."""
        try:
            self.docker_runner = DockerRunner()
            logger.info("✅ Grader initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Grader: {e}")
            raise GraderException(f"Grader init failed: {e}")

    def grade_submission(self, job: WorkerJob) -> WorkerJobResult:
        """
        Grade a single submission.

        Args:
            job: WorkerJob containing user info, exercise metadata, and files

        Returns:
            WorkerJobResult with status, output, score, etc.
        """
        logger.info(f"🎯 Starting grade for job: {job.job_id}")
        logger.info(f"   User: {job.user_id}, Exercise: {job.exercise.slug}")

        temp_dir = None
        try:
            # Step 1: Prepare student files in a temporary directory
            logger.info("📁 Preparing student files...")
            files_dict = {f.filename: f.content for f in job.files}
            temp_dir = create_temp_student_dir(files_dict)
            logger.info(f"   Student dir: {temp_dir}")

            # Step 2: Get sandbox configuration based on exercise type
            logger.info("🔒 Loading sandbox configuration...")
            sandbox_config = get_sandbox_config(job.docker_image)
            sandbox_kwargs = sandbox_config_to_docker_kwargs(sandbox_config)
            logger.info(f"   Sandbox: {job.docker_image}")

            # Step 3: Run the grading container
            logger.info("🚀 Running grading container...")
            output, exit_code = self._run_grader_container(
                docker_image=job.docker_image,
                student_code_dir=temp_dir,
                grader_script_path=job.grader_script_path,
                mount_path=job.mount_path,
                timeout_seconds=job.timeout_seconds,
                sandbox_kwargs=sandbox_kwargs,
            )

            logger.info(f"✅ Container finished (exit_code: {exit_code})")

            # Step 4: Parse output and determine pass/fail
            logger.info("📊 Parsing grader output...")
            status, score = self._parse_grader_output(output, exit_code)

            # Step 5: Create result object
            result = WorkerJobResult(
                job_id=job.job_id,
                user_id=job.user_id,
                exercise_slug=job.exercise.slug,
                status=status,
                output_log=output,
                exit_code=exit_code,
                score=score,
                timestamp=datetime.utcnow(),
            )

            logger.info(f"✅ Grading complete: {status.value} (score: {score})")
            return result

        except DockerRunnerException as e:
            logger.error(f"❌ Docker error during grading: {e}")
            return self._failure_result(job, f"Docker error: {e}", output="")
        except Exception as e:
            logger.error(f"❌ Unexpected error during grading: {e}")
            return self._failure_result(job, f"Grading error: {e}", output="")
        finally:
            # Cleanup: Remove temporary directory
            if temp_dir and Path(temp_dir).exists():
                logger.info(f"🧹 Cleaning up temp dir: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _run_grader_container(
        self,
        docker_image: str,
        student_code_dir: str,
        grader_script_path: str,
        mount_path: str,
        timeout_seconds: int,
        sandbox_kwargs: dict,
    ) -> tuple:
        """
        Run the Docker container with sandbox configuration.

        Args:
            docker_image: Docker image name
            student_code_dir: Host path to student code
            grader_script_path: Grader script path (host file system)
            mount_path: Where to mount student code in container
            timeout_seconds: Container timeout
            sandbox_kwargs: Security/resource limits

        Returns:
            (output, exit_code)
        """
        # Copy grader script into student temp directory
        # (Assuming grader scripts are in data/exercises/[level]/[exercise]/grader/)
        grader_filename = Path(grader_script_path).name
        grader_dest = Path(student_code_dir) / "grader" / grader_filename
        grader_dest.parent.mkdir(parents=True, exist_ok=True)

        if Path(grader_script_path).exists():
            shutil.copy2(grader_script_path, grader_dest)
            logger.info(f"   Copied grader script: {grader_filename}")
        else:
            logger.warning(f"⚠️ Grader script not found: {grader_script_path}")
            # Continue anyway; the container might have it built-in

        # Build the command to run the grader
        # Typically: python /student/grader/test.py
        command = ["python", f"{mount_path}/grader/{grader_filename}"]

        # Run container using Docker runner
        output, exit_code = self.docker_runner.run_container(
            image=docker_image,
            command=command,
            mount_source=student_code_dir,
            mount_target=mount_path,
            timeout_seconds=timeout_seconds,
            env_vars={},  # Can add custom env vars here if needed
            **sandbox_kwargs,  # Apply sandbox restrictions
        )

        return output, exit_code

    @staticmethod
    def _parse_grader_output(output: str, exit_code: int) -> tuple:
        """
        Parse grader output to determine pass/fail and score.

        Supports multiple formats:
        1. JSON format: {"status": "success", "score": 100}
        2. Exit code: exit_code 0 = success, non-zero = failure
        3. Keywords: "PASS" or "FAIL" in output

        Args:
            output: stdout+stderr from grader
            exit_code: Container exit code

        Returns:
            (status, score): (ExerciseStatus enum, int)
        """
        logger.debug("📋 Parsing output...")

        # Try JSON format first
        try:
            # Extract JSON from output (may be mixed with other text)
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                status_str = data.get("status", "failure").lower()
                score = int(data.get("score", 0))
                
                status = ExerciseStatus.SUCCESS if status_str == "success" else ExerciseStatus.FAILURE
                logger.debug(f"   ✅ Parsed JSON: status={status.value}, score={score}")
                return status, score
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        # Try keyword matching
        if "PASS" in output.upper() or "SUCCESS" in output.upper():
            logger.debug("   ✅ Found 'PASS' or 'SUCCESS' keyword")
            return ExerciseStatus.SUCCESS, 100
        elif "FAIL" in output.upper():
            logger.debug("   ❌ Found 'FAIL' keyword")
            return ExerciseStatus.FAILURE, 0

        # Fallback: Check exit code
        if exit_code == 0:
            logger.debug("   ✅ Exit code 0 = success")
            return ExerciseStatus.SUCCESS, 100
        else:
            logger.debug(f"   ❌ Exit code {exit_code} = failure")
            return ExerciseStatus.FAILURE, 0

    @staticmethod
    def _failure_result(job: WorkerJob, error_msg: str, output: str) -> WorkerJobResult:
        """
        Create a failure result.

        Args:
            job: Original WorkerJob
            error_msg: Error message to log
            output: Grader output (if any)

        Returns:
            WorkerJobResult with failure status
        """
        return WorkerJobResult(
            job_id=job.job_id,
            user_id=job.user_id,
            exercise_slug=job.exercise.slug,
            status=ExerciseStatus.FAILURE,
            output_log=f"ERROR: {error_msg}\n{output}",
            exit_code=-1,
            score=0,
            timestamp=datetime.utcnow(),
        )


# ==========================================
# Async wrapper (for background tasks)
# ==========================================

async def grade_submission_async(job: WorkerJob) -> WorkerJobResult:
    """
    Async wrapper for grading (useful with Celery, asyncio, etc).

    Args:
        job: WorkerJob object

    Returns:
        WorkerJobResult
    """
    grader = Grader()
    return grader.grade_submission(job)


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    grader = Grader()
    print("✅ Grader initialized successfully")
