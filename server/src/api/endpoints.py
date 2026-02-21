from fastapi import APIRouter, Request
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ..core.database import db
from ..core.rate_limit import limiter
from ..core.config import settings
from ..models.user import ExerciseHistory
from ..models.exercise import ExerciseState, ExerciseType

router = APIRouter()

PENDING_SUBMISSIONS = {}

class StatusResponse(BaseModel):
    user_id: str
    current_level: int
    current_exercise: Optional[str] = None
    status: str = "ok"
    unlock_at: Optional[datetime] = None
    server_time: datetime

class ExerciseDetailsResponse(BaseModel):
    id: str
    points: int
    subject: str
    type: ExerciseType = ExerciseType.DOCKER

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
        from ..models.user import UserProfile
        user = UserProfile(user_id=user_id, current_level=0)
        db.save_user(user)

    current_exercise_id = None
    level_dir = db.exercises_dir / f"level_{user.current_level:02d}"
    
    server_time = datetime.now()
    
    if level_dir.exists():
        exercises = sorted([
            item.name for item in level_dir.iterdir() 
            if item.is_dir() and item.name.startswith("ex")
        ])
        
        for ex_id in exercises:
            ex_status = user.progress.get(ex_id)
            if ex_status != ExerciseState.SOLVED:
                current_exercise_id = ex_id
                break
        
        if current_exercise_id is None and exercises:
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
        current_exercise=current_exercise_id,
        server_time=server_time
    )

@router.get("/exercises/{exercise_id}", response_model=ExerciseDetailsResponse)
@limiter.limit("240/minute")
async def get_exercise(request: Request, exercise_id: str):
    """
    Returns the metadata and markdown subject for a specific exercise.
    """
    details = db.get_exercise_details(exercise_id)
    if not details:
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
    
    import secrets

    exercise_path = db.get_exercise_path(submission.exercise_id)
    if not exercise_path:
         return SubmissionResponse(
            status="error", 
            message="Internal Error: Exercise path not found.", 
            new_level=user.current_level, 
            score=0
        )

    check_script_path = exercise_path / "check.py"
    if not check_script_path.exists():
        return SubmissionResponse(status="error", message="No grading logic found for this exercise.", new_level=user.current_level, score=0)

    try:
        script_content = check_script_path.read_text()
    except Exception as e:
        return SubmissionResponse(status="error", message=f"Failed to read grader script: {e}", new_level=user.current_level, score=0)

    nonce = secrets.token_hex(16)
    
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
    if verification.nonce not in PENDING_SUBMISSIONS:
        return VerifyResponse(status="error", message="Invalid or expired nonce.", new_level=0, score=0)
    
    submission_data = PENDING_SUBMISSIONS.pop(verification.nonce)
    
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
    
    def sort_key(u):
        last_solve_ts = datetime.max
        for entry in reversed(u.history):
            if entry.status == "solved":
                last_solve_ts = entry.timestamp
                break

        return (-u.total_xp, -u.current_level, last_solve_ts)
    
    users.sort(key=sort_key)
    
    leaderboard = []
    for u in users:
        leaderboard.append(LeaderboardEntry(
            user_id=u.user_id,
            level=u.current_level,
            total_xp=u.total_xp
        ))
    
    return leaderboard

