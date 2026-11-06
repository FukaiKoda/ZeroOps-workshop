"""Run an exercise checker against the user's local workspace."""

import asyncio
import importlib.util
import tempfile
from pathlib import Path
from typing import Any


def _run_grader(script_content: str, exercise_id: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="zeroops-grader-") as temp_dir:
        script_path = Path(temp_dir) / "check.py"
        exercise_path = Path(temp_dir) / exercise_id
        exercise_path.mkdir()
        script_path.write_text(script_content)

        spec = importlib.util.spec_from_file_location(
            f"zeroops_checker_{exercise_id}", script_path
        )
        if spec is None or spec.loader is None:
            return False, "Could not load the exercise checker."

        module: Any = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        setup = getattr(module, "setup", None)
        if setup is not None:
            setup(exercise_path)

        grade = getattr(module, "grade", None)
        if grade is None:
            return False, "Exercise checker does not define grade()."

        result = grade("", exercise_path)
        if not isinstance(result, tuple) or len(result) != 2:
            return False, "Exercise checker returned an invalid result."
        return bool(result[0]), str(result[1])


async def run_local_grader(script_content: str, exercise_id: str) -> tuple[bool, str]:
    """Run blocking Docker checks outside Textual's event loop."""
    return await asyncio.to_thread(_run_grader, script_content, exercise_id)
