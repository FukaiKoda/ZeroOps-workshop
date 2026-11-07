from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    ignore = exercise_path / ".gitignore"
    if not ignore.exists():
        return False, "Create a .gitignore file."
    patterns = set(ignore.read_text().splitlines())
    missing = {"*.log", "build/", ".env"} - patterns
    if missing:
        return False, f".gitignore is missing: {', '.join(sorted(missing))}"
    if not (exercise_path / ".env").exists():
        return False, "Keep .env on disk while removing it from Git tracking."
    return True, "Logs, build output, and .env are ignored while .env remains on disk."