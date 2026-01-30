"""
Shared module - Contracts shared between client and server
"""

from .models import (
    # Enums
    ExerciseStatus,
    GradeStatus,
    SessionStatus,
    # Requests
    SyncRequest,
    LoginRequest,
    GradeRequest,
    StatusRequest,
    # Responses
    LoginResponse,
    SyncResponse,
    GradeResponse,
    StatusResponse,
    GradeResult,
    TestResult,
    ExerciseInfo,
    LevelInfo,
    ExerciseSubject,
    ErrorResponse,
    # User
    UserProfile,
    UserSession,
    ExerciseHistory,
    # Exercise
    ExerciseMeta,
)

__all__ = [
    # Enums
    "ExerciseStatus",
    "GradeStatus",
    "SessionStatus",
    # Requests
    "SyncRequest",
    "LoginRequest",
    "GradeRequest",
    "StatusRequest",
    # Responses
    "LoginResponse",
    "SyncResponse",
    "GradeResponse",
    "StatusResponse",
    "GradeResult",
    "TestResult",
    "ExerciseInfo",
    "LevelInfo",
    "ExerciseSubject",
    "ErrorResponse",
    # User
    "UserProfile",
    "UserSession",
    "ExerciseHistory",
    # Exercise
    "ExerciseMeta",
]

