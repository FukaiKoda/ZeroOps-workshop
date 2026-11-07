from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    title = exercise_path / "title.txt"
    if not title.exists() or title.read_text().strip() != "Pocket Recipes - Italian Quick Meals":
        return False, "Resolve title.txt to exactly: Pocket Recipes - Italian Quick Meals"
    return True, "The merge conflict result is correct. Confirm the rebase and fast-forward history."