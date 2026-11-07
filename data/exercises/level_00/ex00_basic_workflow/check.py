from pathlib import Path
from typing import Tuple


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    pasta = exercise_path / "pasta.txt"
    if not pasta.exists():
        return False, "Create pasta.txt in the exercise repository."
    content = pasta.read_text()
    required = "Pasta: boil water, add pasta, cook 10 minutes"
    if required not in content or "Serve hot" not in content:
        return False, "pasta.txt must contain the recipe and the serving tip."
    return True, "The focused pasta commits produced the expected recipe."