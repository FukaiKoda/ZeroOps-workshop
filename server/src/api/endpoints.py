from fastapi import APIRouter, Request
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ..core.database import db
from ..core.rate_limit import limiter
from ..models.user import ExerciseHistory, UserProfile
from ..models.exercise import ExerciseState, ExerciseType
from . import auth

router = APIRouter()
router.include_router(auth.router)

# In-memory store for pending submissions (nonce -> data)
PENDING_SUBMISSIONS = {}

class StatusResponse(BaseModel):
    user_id: str
    current_level: int
    current_exercise: Optional[str] = None
    status: str = "ok"

class ExerciseDetailsResponse(BaseModel):
    id: str
    points: int
    subject: str
    type: ExerciseType = ExerciseType.DOCKER  # Exercise type: docker, kubernetes, etc.

from ..models.submission import SubmissionRequest, SubmissionResponse, VerifyRequest, VerifyResponse

@router.get("/status/{user_id}", response_model=StatusResponse)
@limiter.limit("240/minute")
async def get_status(request: Request, user_id: str):
    """
    Returns the current status of the user.
    If the user does not exist, a new profile is created (for workshop simplicity).
    """
    user = db.get_user(user_id)
    if not user:
        # User must authenticate first
        return StatusResponse(
            user_id=user_id,
            current_level=0,
            status="error",
            current_exercise=None
        )

    # Determine current exercise based on level
    # Find the first UNSOLVED exercise in the current level
    current_exercise_id = None
    level_dir = db.exercises_dir / f"level_{user.current_level:02d}"
    
    if level_dir.exists():
        # Get all exercises in the level, sorted by name
        exercises = sorted([
            item.name for item in level_dir.iterdir() 
            if item.is_dir() and item.name.startswith("ex")
        ])
        
        # Find the first unsolved exercise
        for ex_id in exercises:
            ex_status = user.progress.get(ex_id)
            if ex_status != ExerciseState.SOLVED:
                current_exercise_id = ex_id
                break
        
        # If all exercises in this level are solved, check if we should level up
        if current_exercise_id is None and exercises:
            # All exercises solved - this means we need to go to next level
            # The level up should have happened in update_user_progress
            # But let's check the next level for exercises
            next_level_dir = db.exercises_dir / f"level_{user.current_level + 1:02d}"
            if next_level_dir.exists():
                next_exercises = sorted([
                    item.name for item in next_level_dir.iterdir() 
                    if item.is_dir() and item.name.startswith("ex")
                ])
                if next_exercises:
                    current_exercise_id = next_exercises[0]
    
    return StatusResponse(
        user_id=user.user_id,
        current_level=user.current_level,
        current_exercise=current_exercise_id
    )

@router.get("/exercises/{exercise_id}", response_model=ExerciseDetailsResponse)
@limiter.limit("240/minute")
async def get_exercise(request: Request, exercise_id: str):
    """
    Returns the metadata and markdown subject for a specific exercise.
    """
    details = db.get_exercise_details(exercise_id)
    if not details:
        # FastAPI would typically raise HTTPException(404)
        return ExerciseDetailsResponse(id=exercise_id, points=0, subject="Exercise not found.", type="python")
        
    meta = details["meta"]
    return ExerciseDetailsResponse(
        id=meta.id,
        points=meta.points,
        subject=details["subject"],
        type=getattr(meta, 'type', 'python')
    )

@router.post("/grade", response_model=SubmissionResponse)
@limiter.limit("60/minute")
async def submit_exercise(request: Request, submission: SubmissionRequest):
    """
    Initiates the grading process.
    Returns the grading script and a nonce for the client to execute.
    """
    user = db.get_user(submission.user_id)
    if not user:
        return SubmissionResponse(status="error", message="User not found", new_level=0, score=0)
    
    # Dynamic Grading Logic using "Strategy Pattern"
    from ..core.loader import load_module_from_path
    import secrets

    exercise_path = db.get_exercise_path(submission.exercise_id)
    if not exercise_path:
         return SubmissionResponse(
            status="error", 
            message="Internal Error: Exercise path not found.", 
            new_level=user.current_level, 
            score=0
        )

    # Check for custom grader (check.py)
    check_script_path = exercise_path / "check.py"
    if not check_script_path.exists():
        return SubmissionResponse(status="error", message="No grading logic found for this exercise.", new_level=user.current_level, score=0)

    # Read the script content
    try:
        script_content = check_script_path.read_text()
    except Exception as e:
        return SubmissionResponse(status="error", message=f"Failed to read grader script: {e}", new_level=user.current_level, score=0)

    # Generate a nonce
    nonce = secrets.token_hex(16)
    
    # Store nonce in a temporary store (For simplicity, using a global dict, but in prod use Redis)
    PENDING_SUBMISSIONS[nonce] = {
        "user_id": submission.user_id,
        "exercise_id": submission.exercise_id,
        "timestamp": datetime.now()
    }

    return SubmissionResponse(
        status="pending",
        message="Grading script prepared. Please execute locally.",
        new_level=user.current_level,
        score=0,
        script_content=script_content,
        nonce=nonce
    )

@router.post("/verify", response_model=VerifyResponse)
@limiter.limit("60/minute")
async def verify_submission(request: Request, verification: VerifyRequest):
    """
    Verifies the result of a client-side grading execution.
    """
    # 1. Validate Nonce
    if verification.nonce not in PENDING_SUBMISSIONS:
        return VerifyResponse(status="error", message="Invalid or expired nonce.", new_level=0, score=0)
    
    submission_data = PENDING_SUBMISSIONS.pop(verification.nonce)
    
    # Check User ID match
    if submission_data["user_id"] != verification.user_id:
        return VerifyResponse(status="error", message="User mismatch.", new_level=0, score=0)
    
    user = db.get_user(verification.user_id)
    if not user:
        return VerifyResponse(status="error", message="User not found.", new_level=0, score=0)

    score = 0
    status = ExerciseState.FAILED
    message = "Failed"

    if verification.result:
        score = 100
        status = ExerciseState.SOLVED
        message = "Correct! " + verification.logs
    else:
        message = "Failed: " + verification.logs

    # Create history entry
    entry = ExerciseHistory(
        ex_id=submission_data["exercise_id"],
        status=status,
        score=score,
        timestamp=datetime.now()
    )

    updated_user = db.update_user_progress(user.user_id, entry)
    
    return VerifyResponse(
        status="success" if score == 100 else "failure",
        message=message,
        new_level=updated_user.current_level if updated_user else user.current_level,
        score=score
    )

class LeaderboardEntry(BaseModel):
    user_id: str
    level: int
    total_xp: int

@router.get("/leaderboard", response_model=list[LeaderboardEntry])
@limiter.limit("60/minute")
async def get_leaderboard(request: Request):
    users = db.get_all_users()
    # Sort by XP descending, then Level descending
    users.sort(key=lambda u: (u.total_xp, u.current_level), reverse=True)
    
    # Take top 10
    top_users = users[:10]
    
    leaderboard = []
    for u in top_users:
        leaderboard.append(LeaderboardEntry(
            user_id=u.user_id,
            level=u.current_level,
            total_xp=u.total_xp
        ))
    
    return leaderboard

