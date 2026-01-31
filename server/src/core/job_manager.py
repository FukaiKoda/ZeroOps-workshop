"""
Job Manager: Queue and execute grading jobs.

This is the bridge between Server-Core and Server-Worker.
Creates WorkerJob objects and calls the grader.
"""

import uuid
import logging
from typing import Optional, Dict
from datetime import datetime
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from schemas import (
    WorkerJob,
    WorkerJobResult,
    ExerciseMeta,
    FileSubmission,
    ExerciseStatus,
    GradingJobStatus,
    ExerciseAttempt,
)
from workers.grader import Grader
from core.storage import Storage

logger = logging.getLogger(__name__)


class JobManager:
    """
    Manages grading job lifecycle.
    
    Workflow:
    1. create_job() - Create WorkerJob
    2. execute_job() - Call grader (runs in background)
    3. get_job_status() - Poll for status
    4. _save_result() - Persist result to storage
    """

    def __init__(self):
        """Initialize job manager."""
        self.jobs: Dict[str, GradingJobStatus] = {}  # In-memory job status
        self.grader: Optional[Grader] = None
        self.storage = Storage()
        logger.info("✅ JobManager initialized")

    def _get_grader(self) -> Optional[Grader]:
        """Lazily initialize the grader to allow server start without Docker."""
        if self.grader is not None:
            return self.grader
        try:
            self.grader = Grader()
            return self.grader
        except Exception as e:
            logger.error(f"❌ Grader init failed: {e}")
            return None

    def create_job(
        self,
        user_id: str,
        exercise: ExerciseMeta,
        files: list[FileSubmission],
    ) -> str:
        """
        Create a new grading job.

        Args:
            user_id: User ID
            exercise: Exercise metadata
            files: Student code files

        Returns:
            job_id: Unique job ID for polling
        """
        job_id = f"job-{uuid.uuid4().hex[:12]}"

        # Create WorkerJob
        worker_job = WorkerJob(
            job_id=job_id,
            user_id=user_id,
            exercise=exercise,
            files=files,
            docker_image=exercise.docker_image,
            grader_script_path=exercise.grader_script_path,
            mount_path=exercise.mount_path,
            timeout_seconds=exercise.timeout_seconds,
        )

        # Store initial status
        status = GradingJobStatus(
            job_id=job_id,
            status=ExerciseStatus.SUBMITTED,
            result=None,
            estimated_wait=exercise.timeout_seconds + 5,
        )
        self.jobs[job_id] = status

        # Store worker job for execution
        self.jobs[f"{job_id}_worker_job"] = worker_job

        logger.info(f"📋 Created job {job_id} for user {user_id}")
        return job_id

    def execute_job(self, job_id: str):
        """
        Execute grading job (runs in background).

        Args:
            job_id: Job ID to execute
        """
        logger.info(f"🚀 Executing job: {job_id}")

        worker_job = self.jobs.get(f"{job_id}_worker_job")
        try:
            # Update status to GRADING
            self.jobs[job_id].status = ExerciseStatus.GRADING

            if not worker_job:
                raise ValueError(f"Worker job not found: {job_id}")

            grader = self._get_grader()
            if not grader:
                raise RuntimeError("Grader unavailable (Docker not running)")

            # Call the grader (YOUR WORKER CODE!)
            result: WorkerJobResult = grader.grade_submission(worker_job)

            # Convert WorkerJobResult to ExerciseAttempt
            attempt = ExerciseAttempt(
                exercise_slug=result.exercise_slug,
                timestamp=result.timestamp,
                status=result.status,
                output_log=result.output_log,
                score=result.score,
            )

            # Update job status
            self.jobs[job_id].status = result.status
            self.jobs[job_id].result = attempt
            self.jobs[job_id].estimated_wait = None

            # Save result to storage (user history)
            self._save_result(worker_job.user_id, attempt)

            logger.info(
                f"✅ Job {job_id} completed: {result.status.value} (score: {result.score})"
            )

        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}", exc_info=True)

            # Mark as FAILURE
            self.jobs[job_id].status = ExerciseStatus.FAILURE
            slug = worker_job.exercise.slug if worker_job else "unknown"
            self.jobs[job_id].result = ExerciseAttempt(
                exercise_slug=slug,
                timestamp=datetime.utcnow(),
                status=ExerciseStatus.FAILURE,
                output_log=f"Error: {str(e)}",
                score=0,
            )

    def get_job_status(self, job_id: str) -> Optional[GradingJobStatus]:
        """
        Get current status of a job.

        Args:
            job_id: Job ID

        Returns:
            GradingJobStatus or None if not found
        """
        return self.jobs.get(job_id)

    def _save_result(self, user_id: str, attempt: ExerciseAttempt):
        """
        Save grading result to user history.

        Args:
            user_id: User ID
            attempt: Exercise attempt result
        """
        try:
            user = self.storage.get_user(user_id)
            if not user:
                logger.warning(f"User {user_id} not found, cannot save result")
                return

            # Add to history
            user.history.append(attempt)

            # Update total score if success
            if attempt.status == ExerciseStatus.SUCCESS:
                user.total_score += attempt.score

            # Update current exercise slug (advance to next)
            # (This is simplified; the Engine should handle progression logic)
            user.current_exercise_slug = attempt.exercise_slug

            # Save updated user
            self.storage.save_user(user)

            logger.info(f"💾 Saved result for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Failed to save result: {e}")
