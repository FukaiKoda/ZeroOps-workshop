from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    return True, "Configuration lab submitted. Verify identity and aliases with git config."