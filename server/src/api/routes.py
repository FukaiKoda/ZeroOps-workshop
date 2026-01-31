"""
API Routes: Handles submission and status endpoints.

Endpoints:
- POST /v1/submit - Submit student code for grading
- GET /v1/status/{job_id} - Check grading status
- GET /v1/me - Get current user profile
- GET /v1/exercise - Get current exercise for user
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from typing import Optional
import logging
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from schemas import (
    SubmitRequest,
    SubmitResponse,
    GradingJobStatus,
    UserProfile,
    ExerciseMeta,
)
from core.job_manager import JobManager
from core.storage import Storage
from core.engine import Engine

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
job_manager = JobManager()
storage = Storage()
engine = Engine(storage)


def _find_exercise_dir(exercise_id: str) -> Optional[Path]:
    """Find exercise directory by id under data/exercises."""
    try:
        for path in engine.exercises_dir.rglob(exercise_id):
            if path.is_dir():
                return path
    except Exception:
        return None
    return None


@router.post("/submit", response_model=SubmitResponse)
async def submit_code(
    request: SubmitRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit student code for grading.
    
    Returns 202 Accepted with job_id for polling.
    """
    logger.info(f"📝 Received submission for exercise: {request.exercise_slug}")
    
    # TODO: Validate session_token (for now, accept all)
    # In production: verify HMAC signature
    
    try:
        # Get user from storage (or create if doesn't exist)
        user = storage.get_or_create_user(request.session_token)
        
        # Get exercise metadata
        exercise = engine.get_exercise(request.exercise_slug)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Check if user can access this exercise (prerequisites met)
        if not engine.can_access_exercise(user, exercise):
            raise HTTPException(
                status_code=403,
                detail="Prerequisites not met for this exercise"
            )
        
        # Create grading job
        job_id = job_manager.create_job(
            user_id=user.user_id,
            exercise=exercise,
            files=request.files,
        )
        
        # Start grading in background
        background_tasks.add_task(
            job_manager.execute_job,
            job_id
        )
        
        logger.info(f"✅ Created job: {job_id}")
        
        return SubmitResponse(
            message="Submission received",
            job_id=job_id,
            status_url=f"/v1/status/{job_id}",
        )
    
    except Exception as e:
        logger.error(f"❌ Submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=GradingJobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a grading job.
    
    Poll this endpoint until status is SUCCESS or FAILURE.
    """
    logger.debug(f"🔍 Checking status for job: {job_id}")
    
    try:
        status = job_manager.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    authorization: Optional[str] = Header(None)
):
    """
    Get current user profile.
    
    Requires: Authorization header with session token.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token (format: "Bearer <token>")
    token = authorization.replace("Bearer ", "")
    
    try:
        user = storage.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exercise", response_model=ExerciseMeta)
async def get_current_exercise(
    authorization: Optional[str] = Header(None)
):
    """
    Get the current exercise for the user.
    
    Returns the next available exercise based on user progress.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        user = storage.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get next exercise from engine
        exercise = engine.get_next_exercise(user)
        if not exercise:
            return {"message": "All exercises completed! 🎉"}
        
        return exercise
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Exercise fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exercises")
async def list_exercises():
    """
    List all available exercises.
    
    For testing/debugging purposes.
    """
    try:
        exercises = engine.list_all_exercises()
        return {"exercises": exercises, "count": len(exercises)}
    except Exception as e:
        logger.error(f"❌ Exercise list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exercises/{exercise_slug}")
async def get_exercise_details(exercise_slug: str):
    """
    Get exercise details and subject text by slug.
    """
    try:
        exercise = engine.get_exercise(exercise_slug)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        subject_text = ""
        exercise_dir = _find_exercise_dir(exercise.id)
        if exercise_dir:
            subject_path = exercise_dir / exercise.subject_md_path
            if subject_path.exists():
                subject_text = subject_path.read_text(encoding="utf-8")

        return {
            "exercise": exercise.model_dump(),
            "subject": subject_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Exercise details failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
