from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class ExerciseState(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    SOLVED = "solved"
    FAILED = "failed"


class ExerciseType(str, Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    INTERACTIVE = "interactive"
    GITHUB_ACTIONS = "github_actions"


class ExerciseSection(str, Enum):
    DOCKER = "docker"
    CI = "ci"


class ExerciseMetadata(BaseModel):
    id: str
    folder: Optional[str] = None
    version: int = 1
    points: int
    requirements: List[str] = []
    setup_script: Optional[str] = None
    test_suite: str = "test_suite.py"
    type: ExerciseType = ExerciseType.DOCKER
    section: Optional[ExerciseSection] = None

    def get_folder_name(self) -> str:
        return self.folder or self.id

    def get_section(self) -> ExerciseSection:
        if self.section:
            return self.section
        return (
            ExerciseSection.CI
            if self.type == ExerciseType.GITHUB_ACTIONS
            else ExerciseSection.DOCKER
        )

