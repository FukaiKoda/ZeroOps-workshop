from pathlib import Path
from typing import Tuple

# Protocol: grade(grader, code, exercise_path) -> (success, message)

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex00_hello:
    1. Gets expected output (cached or from solution.py)
    2. Runs user code against expected output
    """
    
    # Use the grader's built-in helper to resolve expected output
    expected_output = grader.get_expected_output(exercise_path)
    
    if not expected_output:
        return False, "Internal Error: Reference solution missing or failed to generate."
        
    # Run the user code using the grader's sandbox
    exit_code, logs = grader.run_python(code)
    
    if exit_code != 0:
        return False, f"Runtime Error: {logs}"
        
    if expected_output in logs:
        return True, f"Output matched: {logs}"
    else:
        return False, f"Output mismatch. Expected '{expected_output}', got '{logs}'"
