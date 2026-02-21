from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from .exercise import ExerciseState

class ExerciseHistory(BaseModel):
    ex_id: str
    status: ExerciseState
    score: int
    timestamp: datetime

class UserProfile(BaseModel):
    user_id: str
    current_level: int = 0
    total_xp: int = 0
    history: List[ExerciseHistory] = []
    progress: Dict[str, ExerciseState] = {}

