from pathlib import Path
from typing import Tuple

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex01_docker:
    1. Validates that the code is a valid Dockerfile
    2. Builds it (mocked or real)
    """
    
    if not code.strip():
        return False, "No Dockerfile content provided."
        
    # Use grader's dockerfile builder
    success, build_msg = grader.build_dockerfile(code)
    
    return success, build_msg
