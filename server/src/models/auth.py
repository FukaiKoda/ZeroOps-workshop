"""
Pydantic schemas for authentication and user profile API responses.
These are separate from the SQLAlchemy ORM models.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginInitResponse(BaseModel):
    """Returned by GET /v1/auth/login — tells the client where to redirect the browser."""
    auth_url: str
    state: str


class PollResponse(BaseModel):
    """Returned by GET /v1/auth/poll/{state}."""
    status: str        # "pending" | "complete" | "expired"
    token: Optional[str] = None  # JWT session token, present only when complete


class RepositoryInfo(BaseModel):
    """Embedded repository info inside UserProfileResponse."""
    owner: str
    repo: str
    full_name: str
    default_branch: str
    last_commit_hash: Optional[str] = None
    last_synced_at: Optional[datetime] = None


class UserProfileResponse(BaseModel):
    """Returned by GET /v1/auth/me."""
    id: int
    github_id: int
    github_username: str
    github_avatar: str
    github_email: Optional[str] = None
    current_level: int
    current_exercise_id: Optional[str] = None
    total_xp: int
    has_repository: bool
    repository: Optional[RepositoryInfo] = None
    created_at: datetime
