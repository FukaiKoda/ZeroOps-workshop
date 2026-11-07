from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    if not any(exercise_path.iterdir()):
        return False, "Submit the populated repository after connecting it to origin."
    return True, "Repository content submitted. Confirm origin and the up-to-date main branch."