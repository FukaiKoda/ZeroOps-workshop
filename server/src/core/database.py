"""
Exercise content database — flat-file JSON (unchanged from original).
Only serves exercise metadata and scripts from the data/exercises directory.
User management has been moved to SQLite via SQLAlchemy (see core/db.py).
"""

import os
from typing import Optional
from pathlib import Path
from ..models.exercise import ExerciseMetadata


class ExerciseDatabase:
    """
    Read-only access to exercise content stored as flat files.
    Structure: data/exercises/level_XX/ex_id/{meta.json, subject.md, check.py}
    """

    def __init__(self, exercises_dir: str = "data/exercises"):
        self.exercises_dir = Path(exercises_dir)
        self.exercises_dir.mkdir(parents=True, exist_ok=True)

    def get_exercise_meta(self, level: int, ex_id: str) -> Optional[ExerciseMetadata]:
        level_dir = self.exercises_dir / f"level_{level:02d}"
        meta_file = level_dir / ex_id / "meta.json"

        if not meta_file.exists():
            return None

        try:
            import json
            with open(meta_file, "r") as f:
                data = json.load(f)
            return ExerciseMetadata(**data)
        except Exception as e:
            print(f"Error loading exercise {ex_id}: {e}")
            return None

    def get_exercise_details(self, ex_id: str) -> Optional[dict]:
        for level_dir in sorted(self.exercises_dir.iterdir()):
            if not level_dir.is_dir() or not level_dir.name.startswith("level_"):
                continue

            exercise_path = level_dir / ex_id
            if exercise_path.exists():
                import json
                meta = self.get_exercise_meta(int(level_dir.name.split("_")[1]), ex_id)
                if not meta:
                    return None

                subject_file = exercise_path / "subject.md"
                subject_content = ""
                if subject_file.exists():
                    with open(subject_file, "r") as f:
                        subject_content = f.read()

                return {"meta": meta, "subject": subject_content}
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

    def list_exercises_for_level(self, level: int) -> list[str]:
        """Return sorted list of exercise IDs for a given level."""
        level_dir = self.exercises_dir / f"level_{level:02d}"
        if not level_dir.exists():
            return []
        return sorted(
            item.name
            for item in level_dir.iterdir()
            if item.is_dir() and item.name.startswith("ex")
        )

    def level_exists(self, level: int) -> bool:
        return (self.exercises_dir / f"level_{level:02d}").exists()


DEFAULT_EXERCISES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "exercises"
exercise_db = ExerciseDatabase(
    os.getenv("EXERCISES_DIR", str(DEFAULT_EXERCISES_DIR))
)
