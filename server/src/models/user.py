from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from .exercise import ExerciseState

class SessionContext(BaseModel):
    ip: str
    login_time: datetime
    hostname: Optional[str] = None

class ExerciseHistory(BaseModel):
    ex_id: str
    status: ExerciseState
    score: int
    timestamp: datetime

class UserProfile(BaseModel):
    user_id: str
    current_level: int = 0
    total_xp: int = 0
    image_url: Optional[str] = None
    history: List[ExerciseHistory] = []
    session_context: Optional[SessionContext] = None
    
    # Quick lookup for exercise state
    progress: Dict[str, ExerciseState] = {}
