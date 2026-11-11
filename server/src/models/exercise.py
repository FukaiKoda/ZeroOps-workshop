from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class ExerciseState(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    SOLVED = "solved"
    FAILED = "failed"


class ExerciseType(str, Enum):
    GIT = "git"


class ExerciseMetadata(BaseModel):
    id: str
    folder: Optional[str] = None
    version: int = 1
    points: int
    requirements: List[str] = []
    setup_script: Optional[str] = None
    test_suite: str = "test_suite.py"
    type: ExerciseType = ExerciseType.GIT
    requires_remote: bool = False
    remote_path: str | None = None

    def get_folder_name(self) -> str:
        return self.folder or self.id

