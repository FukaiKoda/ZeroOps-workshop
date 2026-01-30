"""
Shared Pydantic Models - API CONTRACTS
These models are shared between client and server.
Any modification here must be communicated to the team.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ============== ENUMS ==============

class ExerciseStatus(str, Enum):
    """Status of an exercise for a user"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    LOCKED = "locked"


class GradeStatus(str, Enum):
    """Status of a grading job"""
    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"


class SessionStatus(str, Enum):
    """Status of a user session"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"


# ============== REQUEST MODELS ==============

class SyncRequest(BaseModel):
    """POST /v1/sync - Request current user state"""
    session_token: str = Field(..., description="User session token")
    client_version: str = Field(..., description="Client version for compatibility check")
    hostname: Optional[str] = Field(None, description="Client hostname")
    username: Optional[str] = Field(None, description="Local username")


class LoginRequest(BaseModel):
    """POST /v1/auth/login - User login"""
    username: str = Field(..., min_length=1, max_length=50)
    password: Optional[str] = Field(None, description="Optional password")


class GradeRequest(BaseModel):
    """POST /v1/grade - Submit an exercise for grading"""
    session_token: str
    exercise_id: str = Field(..., description="ID of the exercise to grade")
    submission_path: str = Field(..., description="Local path or git URL")


class StatusRequest(BaseModel):
    """GET /v1/status/{job_id} - Check grading status"""
    job_id: str


# ============== RESPONSE MODELS ==============

class ExerciseInfo(BaseModel):
    """Information about an exercise"""
    id: str
    name: str
    description: Optional[str] = None
    points: int
    status: ExerciseStatus
    level: int
    requirements: List[str] = []
    subject_url: Optional[str] = None


class LevelInfo(BaseModel):
    """Information about a level"""
    level: int
    name: str
    exercises: List[ExerciseInfo]
    total_points: int
    earned_points: int
    is_complete: bool


class LoginResponse(BaseModel):
    """Response to POST /v1/auth/login"""
    success: bool
    session_token: Optional[str] = None
    user_id: Optional[str] = None
    message: str


class SyncResponse(BaseModel):
    """Response to POST /v1/sync"""
    user_id: str
    username: str
    current_level: int
    current_exercise: Optional[ExerciseInfo] = None
    total_score: int
    max_score: int
    levels: List[LevelInfo] = []
    message: Optional[str] = None
    server_version: str = "0.1.0"


class GradeResponse(BaseModel):
    """Response to POST /v1/grade"""
    job_id: str
    status: GradeStatus
    message: str
    estimated_time: Optional[int] = Field(None, description="Estimated time in seconds")


class TestResult(BaseModel):
    """Result of a single test"""
    name: str
    passed: bool
    message: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


class GradeResult(BaseModel):
    """Detailed result of a grading"""
    exercise_id: str
    status: ExerciseStatus
    score: int
    max_score: int
    feedback: Optional[str] = None
    tests: List[TestResult] = []
    logs: Optional[List[str]] = None
    execution_time: Optional[float] = None


class StatusResponse(BaseModel):
    """Response to GET /v1/status/{job_id}"""
    job_id: str
    status: GradeStatus
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    result: Optional[GradeResult] = None
    new_level: Optional[int] = None
    unlocked_exercises: List[str] = []


class ExerciseSubject(BaseModel):
    """Exercise subject content"""
    exercise_id: str
    name: str
    content: str  # Markdown content
    points: int
    requirements: List[str] = []


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: int


# ============== USER MODELS ==============

class ExerciseHistory(BaseModel):
    """History entry for a completed exercise"""
    exercise_id: str
    status: ExerciseStatus
    score: int
    max_score: int
    attempts: int = 1
    completed_at: Optional[datetime] = None
    last_attempt_at: datetime


class UserSession(BaseModel):
    """User session information"""
    session_token: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    login_time: datetime
    last_activity: datetime
    client_version: Optional[str] = None


class UserProfile(BaseModel):
    """Complete user profile"""
    user_id: str
    username: str
    current_level: int = 0
    total_score: int = 0
    history: Dict[str, ExerciseHistory] = {}  # exercise_id -> history
    sessions: List[UserSession] = []
    created_at: datetime
    updated_at: datetime


# ============== EXERCISE METADATA ==============

class ExerciseMeta(BaseModel):
    """Exercise metadata from meta.json"""
    id: str
    name: Optional[str] = None
    points: int = 10
    requirements: List[str] = []
    setup_script: Optional[str] = None
    test_suite: Optional[str] = None
    timeout: int = 60  # seconds
    allowed_files: List[str] = []
    forbidden_functions: List[str] = []

