from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Identity(BaseModel):
    """Client identity metadata sent with every request."""
    protocol_version: int = Field(..., ge=1)
    username: str
    hostname: str
    client_id: str
    timestamp: str


class SyncResponse(BaseModel):
    """Response payload for /v1/sync."""
    level: int
    total_levels: int


class StarterFile(BaseModel):
    """Represents a starter file path and content (unused by client)."""
    path: str
    content: str


class SubjectResponse(BaseModel):
    """Response payload for /v1/subject."""
    level: int
    total_levels: int
    subject: str
    starter_files: List[StarterFile]


class TestSpecConstraints(BaseModel):
    """Constraints that the client test runner must enforce."""
    timeout_seconds: int = Field(..., ge=1)


class TestSpec(BaseModel):
    """Test specification describing deterministic cases to run."""
    level: int
    entrypoint: str
    function: str
    cases: List[Dict[str, Any]]
    constraints: TestSpecConstraints


class TestSpecResponse(BaseModel):
    """Response payload for /v1/testspec."""
    level: int
    testspec: TestSpec
    constraints: TestSpecConstraints


class TestCaseResult(BaseModel):
    """Per-test-case result from the client runner."""
    name: str
    pass_: bool = Field(..., alias="pass")
    message: str = ""

    class Config:
        allow_population_by_field_name = True


class TestResults(BaseModel):
    """Aggregate results reported by the client."""
    level: int
    pass_: bool = Field(..., alias="pass")
    tests: List[TestCaseResult]
    runtime_ms: int
    error: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class SubmitRequest(BaseModel):
    """Request body for /v1/submit."""
    identity: Identity
    results: TestResults


class SubmitResponse(BaseModel):
    """Response payload for /v1/submit."""
    level: int
    feedback: str


class AdminUser(BaseModel):
    """Admin view of a user record."""
    username: str
    level: int


class AdminUsersResponse(BaseModel):
    """Response payload for /v1/admin/users."""
    users: List[AdminUser]
