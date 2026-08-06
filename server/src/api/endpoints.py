"""
Core exercise endpoints — status, exercise details, grading and leaderboard.
User identity now comes from the JWT-authenticated User ORM object.
"""

from fastapi import APIRouter, Request, Depends
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.db import get_db
from ..core.database import exercise_db
from ..core.rate_limit import limiter
from ..core.github_repo import fetch_workflow_files, fetch_directory
from ..models.db_user import User
from ..models.db_submission import ExerciseSubmission
from ..models.exercise import ExerciseState, ExerciseType
from ..models.submission import (
    SubmissionRequest,
    SubmissionResponse,
    VerifyRequest,
    VerifyResponse,
)
from .auth import get_current_user

router = APIRouter()

# In-memory nonce store — same pattern as original
PENDING_SUBMISSIONS: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class StatusResponse(BaseModel):
    user_id: str
    github_username: str
    current_level: int
    current_exercise: Optional[str] = None
    status: str = "ok"
    server_time: datetime


class ExerciseDetailsResponse(BaseModel):
    id: str
    folder: str = ""
    version: int = 1
    points: int
    subject: str
    type: ExerciseType = ExerciseType.DOCKER



class SubmissionHistoryEntry(BaseModel):
    exercise_id: str
    status: str
    score: int
    feedback: Optional[str]
    commit_hash: Optional[str]
    submitted_at: datetime


# ---------------------------------------------------------------------------
# GET /v1/status/{user_id}
# For backwards compatibility, accepts github_username as user_id.
# Protected: requires JWT.
# ---------------------------------------------------------------------------

@router.get("/status/{user_id}", response_model=StatusResponse)
@limiter.limit("240/minute")
async def get_status(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the current status of the authenticated user.
    `user_id` path param is kept for client compatibility but the identity
    comes from the JWT — students cannot query other users' status.
    """
    current_exercise_id = _find_current_exercise(current_user)

    return StatusResponse(
        user_id=str(current_user.id),
        github_username=current_user.github_username,
        current_level=current_user.current_level,
        current_exercise=current_exercise_id,
        server_time=datetime.now(),
    )


# ---------------------------------------------------------------------------
# GET /v1/exercises/{exercise_id}
# ---------------------------------------------------------------------------

@router.get("/exercises/{exercise_id}", response_model=ExerciseDetailsResponse)
@limiter.limit("240/minute")
async def get_exercise(request: Request, exercise_id: str):
    """Returns the metadata and markdown subject for a specific exercise."""
    details = exercise_db.get_exercise_details(exercise_id)
    if not details:
        return ExerciseDetailsResponse(
            id=exercise_id, folder=exercise_id, version=1, points=0, subject="Exercise not found.", type="python"
        )

    meta = details["meta"]
    folder_name = getattr(meta, "folder", None) or (meta.get_folder_name() if hasattr(meta, "get_folder_name") else meta.id)
    version_num = getattr(meta, "version", 1)
    return ExerciseDetailsResponse(
        id=meta.id,
        folder=folder_name,
        version=version_num,
        points=meta.points,
        subject=details["subject"],
        type=getattr(meta, "type", "python"),
    )


# ---------------------------------------------------------------------------
# POST /v1/grade
# ---------------------------------------------------------------------------

@router.post("/grade", response_model=SubmissionResponse)
@limiter.limit("60/minute")
async def submit_exercise(
    request: Request,
    submission: SubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiates the grading process.
    - If user has a linked repository: grades server-side by fetching the exercise
      folder from the student's repository and running check.py in a temp workspace.
    - For unlinked repositories / local exercises: returns script content + nonce for local execution.
    """
    import secrets

    exercise_path = exercise_db.get_exercise_path(submission.exercise_id)
    if not exercise_path:
        return SubmissionResponse(
            status="error",
            message="Internal Error: Exercise path not found.",
            new_level=current_user.current_level,
            score=0,
        )

    check_script_path = exercise_path / "check.py"
    if not check_script_path.exists():
        return SubmissionResponse(
            status="error",
            message="No grading logic found for this exercise.",
            new_level=current_user.current_level,
            score=0,
        )

    details = exercise_db.get_exercise_details(submission.exercise_id)
    exercise_type = getattr(details["meta"], "type", None) if details else None

    # Server-side repository folder-scoped grading flow
    if current_user.repository or exercise_type == ExerciseType.GITHUB_ACTIONS:
        return await grade_submission(
            db=db,
            current_user=current_user,
            exercise_path=exercise_path,
            check_script_path=check_script_path,
            exercise_id=submission.exercise_id,
            commit_hash=submission.commit_hash,
            details=details,
        )


    # -----------------------------------------------------------------
    # All other exercise types: client-side grading flow
    # -----------------------------------------------------------------
    try:
        script_content = check_script_path.read_text()
    except Exception as e:
        return SubmissionResponse(
            status="error",
            message=f"Failed to read grader script: {e}",
            new_level=current_user.current_level,
            score=0,
        )

    nonce = secrets.token_hex(16)
    PENDING_SUBMISSIONS[nonce] = {
        "user_id": current_user.id,
        "exercise_id": submission.exercise_id,
        "commit_hash": submission.commit_hash,
        "timestamp": datetime.now(),
    }

    return SubmissionResponse(
        status="pending",
        message="Grading script prepared. Please execute locally.",
        new_level=current_user.current_level,
        score=0,
        script_content=script_content,
        nonce=nonce,
    )


# ---------------------------------------------------------------------------
# POST /v1/verify
# ---------------------------------------------------------------------------

@router.post("/verify", response_model=VerifyResponse)
@limiter.limit("60/minute")
async def verify_submission(
    request: Request,
    verification: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verifies the result of a client-side grading execution."""
    if verification.nonce not in PENDING_SUBMISSIONS:
        return VerifyResponse(
            status="error", message="Invalid or expired nonce.", new_level=0, score=0
        )

    submission_data = PENDING_SUBMISSIONS.pop(verification.nonce)

    # Nonce must belong to the authenticated user
    if submission_data["user_id"] != current_user.id:
        return VerifyResponse(
            status="error", message="User mismatch.", new_level=0, score=0
        )

    score = 0
    status = "failed"
    message = "Failed"

    if verification.result:
        score = 100
        status = "passed"
        message = "Correct! " + verification.logs
    else:
        message = "Failed: " + verification.logs

    # Determine commit hash — prefer what the verify request carries,
    # fall back to what was stored at grade time
    commit_hash = (
        verification.commit_hash
        or submission_data.get("commit_hash")
    )

    # Persist submission record
    submission_record = ExerciseSubmission(
        user_id=current_user.id,
        exercise_id=submission_data["exercise_id"],
        status=status,
        score=score,
        feedback=verification.logs,
        commit_hash=commit_hash,
    )
    db.add(submission_record)

    # Update user XP and level progression
    new_level = await _update_user_progress(
        db, current_user, submission_data["exercise_id"], score
    )

    await db.commit()

    return VerifyResponse(
        status="success" if score == 100 else "failure",
        message=message,
        new_level=new_level,
        score=score,
    )


# ---------------------------------------------------------------------------
# GET /v1/leaderboard
# ---------------------------------------------------------------------------

class LeaderboardEntry(BaseModel):
    user_id: str
    github_username: str
    level: int
    total_xp: int


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
@limiter.limit("60/minute")
async def get_leaderboard(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).order_by(User.total_xp.desc(), User.current_level.desc())
    )
    users = result.scalars().all()

    return [
        LeaderboardEntry(
            user_id=str(u.id),
            github_username=u.github_username,
            level=u.current_level,
            total_xp=u.total_xp,
        )
        for u in users
    ]


# ---------------------------------------------------------------------------
# GET /v1/submissions/{user_id}
# ---------------------------------------------------------------------------

@router.get("/submissions/{user_id}", response_model=list[SubmissionHistoryEntry])
@limiter.limit("60/minute")
async def get_submissions(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all submission history for the authenticated user."""
    result = await db.execute(
        select(ExerciseSubmission)
        .where(ExerciseSubmission.user_id == current_user.id)
        .order_by(ExerciseSubmission.submitted_at.desc())
    )
    submissions = result.scalars().all()

    return [
        SubmissionHistoryEntry(
            exercise_id=s.exercise_id,
            status=s.status,
            score=s.score,
            feedback=s.feedback,
            commit_hash=s.commit_hash,
            submitted_at=s.submitted_at,
        )
        for s in submissions
    ]


# ---------------------------------------------------------------------------
# Generic Server-Side Grader (Folder-Scoped & Isolated Workspace Lifecycle)
# ---------------------------------------------------------------------------

async def grade_submission(
    db: AsyncSession,
    current_user: User,
    exercise_path,
    check_script_path,
    exercise_id: str,
    commit_hash: Optional[str],
    details: dict,
) -> SubmissionResponse:
    """
    Grade an exercise using the isolated workspace lifecycle:
    1. Determine exercise target folder (e.g. 'ex00_hello_workflow') from metadata.
    2. Fetch files strictly from student's repository directory ('folder/').
    3. Write files into a clean temporary workspace (/tmp/zeroops-grade-XXXX/).
    4. Execute check.py's grade(code, exercise_path=tmp_dir) with exercise_path set to the isolated temp directory.
    5. Cleanly delete the temporary directory post-execution.
    6. Persist submission outcome independently for exercise_id.
    """
    import sys
    import tempfile
    import importlib.util
    from pathlib import Path as _Path

    # Ensure the student has a linked repository
    repo = current_user.repository
    if not repo:
        return SubmissionResponse(
            status="error",
            message="No repository linked. Please link your GitHub repository first.",
            new_level=current_user.current_level,
            score=0,
        )

    if not current_user.access_token:
        return SubmissionResponse(
            status="error",
            message="No GitHub token found. Please log out and log in again.",
            new_level=current_user.current_level,
            score=0,
        )

    meta = details.get("meta") if details else None
    if meta and hasattr(meta, "get_folder_name"):
        folder_name = meta.get_folder_name()
    elif meta and getattr(meta, "folder", None):
        folder_name = meta.folder
    else:
        folder_name = exercise_id

    # Fetch files strictly inside the exercise folder from student's GitHub repo
    exercise_files = await fetch_directory(
        owner=repo.owner,
        repo=repo.repo,
        directory_path=folder_name,
        token=current_user.access_token,
    )

    if not exercise_files:
        return SubmissionResponse(
            status="failure",
            message=(
                f"Directory '{folder_name}' not found in your repository '{repo.full_name}'.\n"
                f"Please create the folder '{folder_name}/' in your repository, add your solution files, commit, push, and submit again."
            ),
            new_level=current_user.current_level,
            score=0,
        )

    # Create temporary isolated workspace (guaranteed cleanup)
    with tempfile.TemporaryDirectory(prefix="zeroops-grade-") as tmp_dir_str:
        tmp_workspace = _Path(tmp_dir_str)

        # Write fetched exercise files into the isolated temp workspace
        combined_code_lines = []
        for rel_path, content in exercise_files.items():
            target_file = tmp_workspace / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(content)
            combined_code_lines.append(f"# === {rel_path} ===\n{content}")

        combined_code = "\n---\n".join(combined_code_lines)

        # Dynamically load check.py and execute grade(code, exercise_path=tmp_workspace)
        try:
            spec = importlib.util.spec_from_file_location("check_module", check_script_path)
            check_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(check_module)
            success, feedback = check_module.grade(combined_code, tmp_workspace)
        except Exception as e:
            return SubmissionResponse(
                status="error",
                message=f"Grader error: {e}",
                new_level=current_user.current_level,
                score=0,
            )

    score = 100 if success else 0
    status = "passed" if success else "failed"

    # Persist submission record
    submission_record = ExerciseSubmission(
        user_id=current_user.id,
        exercise_id=exercise_id,
        status=status,
        score=score,
        feedback=feedback,
        commit_hash=commit_hash,
    )
    db.add(submission_record)

    new_level = await _update_user_progress(db, current_user, exercise_id, score)
    await db.commit()

    return SubmissionResponse(
        status="success" if success else "failure",
        message=feedback,
        new_level=new_level,
        score=score,
    )



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_current_exercise(user: User) -> Optional[str]:
    """
    Find the first unsolved exercise for the user's current level.
    Falls back to the first exercise of the next level if all are solved.
    """
    # Build a progress dict from submission history (latest status per exercise)
    progress: dict[str, str] = {}
    for sub in sorted(user.submissions, key=lambda s: s.submitted_at):
        progress[sub.exercise_id] = sub.status

    for level_offset in range(2):
        level = user.current_level + level_offset
        exercises = exercise_db.list_exercises_for_level(level)
        for ex_id in exercises:
            if progress.get(ex_id) != "passed":
                return ex_id

    return None


async def _update_user_progress(
    db: AsyncSession,
    user: User,
    exercise_id: str,
    score: int,
) -> int:
    """
    Update user's XP and check if they've completed the current level.
    Returns the new level.
    """
    if score > 0:
        # Award XP from exercise metadata
        details = exercise_db.get_exercise_details(exercise_id)
        if details:
            user.total_xp += details["meta"].points

        # Check if all exercises in the current level are now solved
        exercises = exercise_db.list_exercises_for_level(user.current_level)
        if exercises:
            # Re-query submissions to get fresh state
            result = await db.execute(
                select(ExerciseSubmission)
                .where(
                    ExerciseSubmission.user_id == user.id,
                    ExerciseSubmission.status == "passed",
                )
            )
            solved = {s.exercise_id for s in result.scalars().all()}
            solved.add(exercise_id)  # include current

            if all(ex in solved for ex in exercises):
                if exercise_db.level_exists(user.current_level + 1):
                    user.current_level += 1

    return user.current_level
