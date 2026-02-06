from fastapi import APIRouter
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ..core.database import db
from ..models.user import ExerciseHistory, UserProfile
from ..models.exercise import ExerciseState, ExerciseType
from . import auth

router = APIRouter()
router.include_router(auth.router)

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

class SubmissionRequest(BaseModel):
    user_id: str
    exercise_id: str
    code: Optional[str] = None  # In real world, this might be a git URL or file content

class SubmissionResponse(BaseModel):
    status: str
    message: str
    new_level: int
    score: int


@router.get("/status/{user_id}", response_model=StatusResponse)
async def get_status(user_id: str):
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
async def get_exercise(exercise_id: str):
    """
    Returns the metadata and markdown subject for a specific exercise.
    """
    details = db.get_exercise_details(exercise_id)
    if not details:
        # FastAPI would typically raise HTTPException(404)
        return ExerciseDetailsResponse(id=exercise_id, points=0, subject="Exercise not found.", type=ExerciseType.DOCKER)
        
    meta = details["meta"]
    return ExerciseDetailsResponse(
        id=meta.id,
        points=meta.points,
        subject=details["subject"],
        type=getattr(meta, 'type', ExerciseType.DOCKER)  # Get type from meta, default to docker
    )

@router.post("/grade", response_model=SubmissionResponse)
async def submit_exercise(request: SubmissionRequest):
    """
    Mock grading endpoint.
    Checks if the submission is valid for the current level.
    """
    user = db.get_user(request.user_id)
    if not user:
        return SubmissionResponse(status="error", message="User not found", new_level=0, score=0)
    
    score = 0
    status = ExerciseState.LOCKED
    message = "Failed"

    # Dynamic Grading Logic using "Strategy Pattern"
    from ..core.loader import load_module_from_path

    exercise_path = db.get_exercise_path(request.exercise_id)
    if not exercise_path:
         return SubmissionResponse(
            status="error", 
            message="Internal Error: Exercise path not found.", 
            new_level=user.current_level, 
            score=0
        )

    # Check for custom grader (check.py)
    check_script = exercise_path / "check.py"
    checker_module = load_module_from_path(f"check_{request.exercise_id}", check_script)
    
    if checker_module and hasattr(checker_module, "grade"):
        # Use the custom grader
        try:
            # We pass the 'grader' instance and the user code (and maybe db/exercise_path if needed)
            # The protocol is grade(code, exercise_path) -> (success, message)
            
            # BLOCKING CALL FIX:
            # The grading logic involves synchronous Docker calls (subprocess/sockets).
            # We must run this in a thread pool to avoid blocking the main asyncio event loop.
            from fastapi.concurrency import run_in_threadpool
            
            success, result_msg = await run_in_threadpool(
                checker_module.grade, 
                request.code or "", 
                exercise_path
            )
            
            if success:
                 score = 100
                 status = ExerciseState.SOLVED
                 message = "Correct! " + result_msg
            else:
                 message = "Failed: " + result_msg
                 
        except Exception as e:
            message = f"Grader Script Error: {e}"
    else:
        message = "No grading logic found for this exercise."

    # Create history entry
    entry = ExerciseHistory(
        ex_id=request.exercise_id,
        status=status,
        score=score,
        timestamp=datetime.now()
    )

    updated_user = db.update_user_progress(user.user_id, entry)
    
    return SubmissionResponse(
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
async def get_leaderboard():
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

