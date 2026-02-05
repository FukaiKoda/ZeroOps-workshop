import json
import os
from typing import Optional
from pathlib import Path
from ..models.user import UserProfile, ExerciseHistory
from ..models.exercise import ExerciseMetadata, ExerciseState

class JSONDatabase:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"
        self.exercises_dir = self.data_dir / "exercises"
        
        # Ensure directories exist
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.exercises_dir.mkdir(parents=True, exist_ok=True)

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        user_file = self.users_dir / f"{user_id}.json"
        if not user_file.exists():
            return None
        
        try:
            with open(user_file, "r") as f:
                data = json.load(f)
            return UserProfile(**data)
        except Exception as e:
            print(f"Error loading user {user_id}: {e}")
            return None

    def save_user(self, user: UserProfile):
        user_file = self.users_dir / f"{user.user_id}.json"
        with open(user_file, "w") as f:
            f.write(user.model_dump_json(indent=2))

    def get_exercise_meta(self, level: int, ex_id: str) -> Optional[ExerciseMetadata]:
        # Structure: data/exercises/level_XX/ex_id/meta.json
        level_dir = self.exercises_dir / f"level_{level:02d}"
        meta_file = level_dir / ex_id / "meta.json"
        
        if not meta_file.exists():
            return None
            
        try:
            with open(meta_file, "r") as f:
                data = json.load(f)
            return ExerciseMetadata(**data)
        except Exception as e:
            print(f"Error loading exercise {ex_id}: {e}")
            return None

    def get_exercise_details(self, ex_id: str) -> Optional[dict]:
        # Scan all levels to find the exercise
        # Naive search for now
        for level_dir in sorted(self.exercises_dir.iterdir()):
            if not level_dir.is_dir() or not level_dir.name.startswith("level_"):
                continue
                
            exercise_path = level_dir / ex_id
            if exercise_path.exists():
                meta = self.get_exercise_meta(int(level_dir.name.split("_")[1]), ex_id)
                if not meta:
                    return None
                    
                subject_file = exercise_path / "subject.md"
                subject_content = ""
                if subject_file.exists():
                    with open(subject_file, "r") as f:
                        subject_content = f.read()
                        
                return {
                    "meta": meta,
                    "subject": subject_content
                }
        return None

    def get_exercise_path(self, ex_id: str) -> Optional[Path]:
        """Returns the absolute path to the directory of an exercise."""
        for level_dir in sorted(self.exercises_dir.iterdir()):
             if not level_dir.is_dir() or not level_dir.name.startswith("level_"):
                 continue
             
             exercise_path = level_dir / ex_id
             if exercise_path.exists():
                 return exercise_path
        return None

    def update_user_progress(self, user_id: str, history_entry: ExerciseHistory) -> Optional[UserProfile]:
        user = self.get_user(user_id)
        if not user:
            return None
        
        # Add to history
        user.history.append(history_entry)
        
        # Update progress map
        user.progress[history_entry.ex_id] = history_entry.status
        
        # Level up logic: Only level up if ALL exercises in current level are SOLVED
        if history_entry.status == ExerciseState.SOLVED:
            # Find the exercise meta to get points
            found_meta = None
            exercise_level = None
            
            for level_dir in self.exercises_dir.iterdir():
                if level_dir.is_dir() and level_dir.name.startswith("level_"):
                    potential_path = level_dir / history_entry.ex_id / "meta.json"
                    if potential_path.exists():
                        try:
                            with open(potential_path, "r") as f:
                                found_meta = ExerciseMetadata(**json.load(f))
                            exercise_level = int(level_dir.name.split("_")[1])
                            break
                        except:
                            pass
            
            # Award XP for solving the exercise
            if found_meta:
                user.total_xp += found_meta.points
            
            # Check if ALL exercises in the current level are solved
            current_level_dir = self.exercises_dir / f"level_{user.current_level:02d}"
            if current_level_dir.exists():
                # Get all exercises in the current level
                all_exercises = [
                    item.name for item in current_level_dir.iterdir() 
                    if item.is_dir() and item.name.startswith("ex")
                ]
                
                # Check if all are solved
                all_solved = True
                for ex_id in all_exercises:
                    if user.progress.get(ex_id) != ExerciseState.SOLVED:
                        all_solved = False
                        break
                
                # Level up only if all exercises in the level are solved
                if all_solved and all_exercises:
                    user.current_level += 1

        self.save_user(user)
        return user

    def get_all_users(self) -> list[UserProfile]:
        users = []
        for user_file in self.users_dir.glob("*.json"):
            try:
                with open(user_file, "r") as f:
                    data = json.load(f)
                users.append(UserProfile(**data))
            except Exception as e:
                print(f"Error loading user {user_file}: {e}")
        return users


# Global instance (can be overridden for testing)
# Default data directory relative to this file:
# PROJECT_ROOT/server/src/core/database.py -> ... -> PROJECT_ROOT/data
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
db = JSONDatabase(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))
