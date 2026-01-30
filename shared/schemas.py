from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# ==========================================
# 1. Enums (Shared Vocabulary)
# ==========================================

class ExerciseStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    SUBMITTED = "submitted"  # Pending grading
    GRADING = "grading"      # Worker is running
    SUCCESS = "success"
    FAILURE = "failure"

class TechStack(str, Enum):
    C = "c"
    PYTHON = "python"
    BASH = "bash"
    DOCKER = "docker"

# ==========================================
# 2. File System & Metadata Models
# ==========================================

class ExerciseMeta(BaseModel):
    """
    Represents the meta.json found in each exercise folder.
    Used by Server-Core to validate requests and by Client to show requirements.
    """
    id: str = Field(..., description="Unique ID, e.g., 'ex00_hello'")
    slug: str = Field(..., description="Slug for routing, e.g., 'docker-01'")
    title: str = Field(..., description="Human-readable title")
    points: int = 100
    stack: TechStack
    
    # Exercise Constraints
    allowed_files: List[str] = Field(default_factory=list, description="Files strictly required for submission")
    forbidden_functions: Optional[List[str]] = None
    requirements: List[str] = Field(default_factory=list, description="e.g., ['ex00_hello'] must be passed first")
    
    # Docker & Grading
    docker_image: str = Field(..., description="e.g., 'python-runner:latest' or 'c-runner:latest'")
    grader_script_path: str = Field(..., description="Path in grader/ folder, e.g., 'grader/test.py'")
    mount_path: str = Field(default="/student", description="Where student code is mounted in container")
    
    # Execution
    timeout_seconds: int = 10
    
    # Metadata
    subject_md_path: str = Field(default="subject.md", description="Path to exercise instructions")


class FileSubmission(BaseModel):
    """
    Represents a single file being uploaded.
    """
    filename: str
    content: str  # Raw text (code files are text-based)


# ==========================================
# 3. User & State Models (Database)
# ==========================================

class ExerciseAttempt(BaseModel):
    """
    History record of a single attempt.
    """
    exercise_slug: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ExerciseStatus
    output_log: Optional[str] = None  # The compiler/linter output
    score: int = 0


class UserProfile(BaseModel):
    """
    Represents the user.json stored in the DB.
    Persistent user data only (no ephemeral session tokens).
    """
    user_id: str = Field(..., description="Unique identifier, e.g., 'hatim_42'")
    username: str
    current_level: int = 0
    current_exercise_slug: str
    total_score: int = 0
    history: List[ExerciseAttempt] = Field(default_factory=list)
    
    # Metadata
    last_login_ip: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionToken(BaseModel):
    """
    Ephemeral session tokens (stored separately, with TTL).
    NOT part of UserProfile to allow horizontal scaling.
    """
    token: str = Field(..., description="HMAC-signed token")
    user_id: str
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    ip_address: str


# ==========================================
# 4. API Communication Models (Req/Res)
# ==========================================

class SubmitRequest(BaseModel):
    """
    Payload for POST /v1/submit
    """
    session_token: str
    exercise_slug: str
    files: List[FileSubmission]
    client_version: str


class SubmitResponse(BaseModel):
    """
    Response for POST /v1/submit (202 Accepted)
    """
    message: str = "Submission received"
    job_id: str
    status_url: str  # URL to poll, e.g., /v1/status/{job_id}


class GradingJobStatus(BaseModel):
    """
    Response for GET /v1/status/{job_id}
    """
    job_id: str
    status: ExerciseStatus  # SUBMITTED -> GRADING -> SUCCESS/FAILURE
    result: Optional[ExerciseAttempt] = None  # Populated only when finished
    estimated_wait: Optional[int] = None


# ==========================================
# 5. Worker Payload (Internal)
# ==========================================

class WorkerJob(BaseModel):
    """
    What Server-Core puts into the Queue for Server-Worker.
    Contains everything needed to execute grading in isolation.
    """
    job_id: str
    user_id: str
    exercise: ExerciseMeta
    files: List[FileSubmission]
    
    # Docker Execution Context
    docker_image: str = Field(..., description="e.g., 'python-runner:latest'")
    grader_script_path: str = Field(..., description="Full path to grader script on host")
    mount_path: str = Field(default="/student", description="Mount point inside container")
    timeout_seconds: int = Field(default=10)


class WorkerJobResult(BaseModel):
    """
    Result returned by the Worker back to Server-Core.
    """
    job_id: str
    user_id: str
    exercise_slug: str
    status: ExerciseStatus
    output_log: str  # stdout + stderr from container
    exit_code: int
    score: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# 6. Notes on Concurrency & Persistence
# ==========================================
"""
⚠️ IMPORTANT: File Locking for JSON Storage

Since the users.json (and exercise history) is JSON-based, multiple
concurrent writes will corrupt the file. To prevent this:

Option 1 (Recommended): Use fcntl.flock() on Unix/Linux
  - Lock the file before reading
  - Update in memory
  - Write back
  - Release lock

Option 2: Use a lightweight wrapper like TinyDB (file-based)
  - Handles locking internally
  - Drop-in replacement for JSON

Option 3: Migrate to SQLite (disguised as a file)
  - ACID transactions
  - Better performance

For Sprint 1: Implement Option 1 (fcntl.flock) in Server-Core.
"""
