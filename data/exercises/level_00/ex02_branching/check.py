from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    dessert = exercise_path / "dessert.txt"
    if not dessert.exists():
        return False, "Create and commit dessert.txt on feature/dessert."
    return True, "The dessert branch contains dessert.txt. Confirm main remains unchanged."