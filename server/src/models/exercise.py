from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class ExerciseState(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    SOLVED = "solved"


class ExerciseType(str, Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"

class ExerciseMetadata(BaseModel):
    id: str
    points: int
    requirements: List[str] = []
    setup_script: Optional[str] = None
    test_suite: str = "test_suite.py"
    type: ExerciseType = ExerciseType.DOCKER # Default type
