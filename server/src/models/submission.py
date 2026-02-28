from pydantic import BaseModel
from typing import Optional


class SubmissionRequest(BaseModel):
    user_id: str
    exercise_id: str
    code: Optional[str] = None


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


class VerifyResponse(BaseModel):
    status: str
    message: str
    new_level: int
    score: int
