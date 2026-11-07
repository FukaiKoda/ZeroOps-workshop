from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    progress = exercise_path / "progress.txt"
    if not progress.exists() or len(progress.read_text().splitlines()) != 3:
        return False, "Restore progress.txt so it contains all three steps."
    return True, "All three progress steps are present after recovery."