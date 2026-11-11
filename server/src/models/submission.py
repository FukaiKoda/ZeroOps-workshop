from pydantic import BaseModel, Field
from typing import Optional


class SubmissionRequest(BaseModel):
    user_id: str
    exercise_id: str
    code: Optional[str] = None
    files: dict[str, str] = Field(default_factory=dict)
    commit_hash: Optional[str] = None  # Latest commit hash from synced repo


class SubmissionResponse(BaseModel):
    status: str
    message: str
    new_level: int
    score: int
    script_content: Optional[str] = None
    nonce: Optional[str] = None


class VerifyRequest(BaseModel):
    user_id: str
    nonce: str
    result: bool
    logs: str
    commit_hash: Optional[str] = None  # Passed through from SubmissionRequest


class VerifyResponse(BaseModel):
    status: str
    message: str
    new_level: int
    score: int
