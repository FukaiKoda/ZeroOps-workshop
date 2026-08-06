"""Validator for Level 00 Exercise 00 — Hello Workflow."""

import yaml
from pathlib import Path
from typing import Tuple, List, Any, Dict


def _find_workflow_files(cwd: Path, filename_hint: str = "hello") -> List[Path]:
    """Find workflow files inside the isolated exercise folder, preferring ones matching hint."""
    files: List[Path] = []
    search_dirs = [cwd, cwd / ".github" / "workflows", cwd / "workflows"]
    for d in search_dirs:
        if d.exists() and d.is_dir():
            for ext in ["*.yml", "*.yaml"]:
                files.extend(d.glob(ext))
    # Deduplicate while preserving order
    seen = set()
    unique_files = []
    for f in files:
        if f.resolve() not in seen:
            seen.add(f.resolve())
            unique_files.append(f)
    return sorted(unique_files, key=lambda f: (0 if filename_hint in f.stem.lower() else 1, f.name))



def _parse_yaml(content: str) -> Tuple[bool, Any, str]:
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return False, None, "YAML root must be a dictionary."
        return True, data, ""
    except yaml.YAMLError as e:
        return False, None, f"YAML Syntax Error: {e}"


def _validate_hello_workflow(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []

    # --- Check workflow name ---
    wf_name = str(data.get("name", "")).strip()
    if not wf_name:
        errors.append("Missing 'name:' field. Set it to 'Hello ZeroOps'.")
    elif "hello zeroops" not in wf_name.lower():
        errors.append(
            f"Workflow name should be 'Hello ZeroOps', got '{wf_name}'."
        )

    # --- Check trigger ('on:') ---
    # PyYAML parses the bare key 'on' as the boolean True
    trigger = data.get("on") or data.get(True) or data.get("true")
    if trigger is None:
        errors.append(
            "Missing trigger 'on:'. Add 'on: push' to run the workflow on every push."
        )
    else:
        trigger_str = str(trigger).lower()
        # Acceptable: "push", "[push]", {"push": null}, etc.
        if "push" not in trigger_str:
            errors.append(
                f"Trigger must include 'push'. Got: {trigger}"
            )

    # --- Check jobs ---
    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        errors.append("Missing 'jobs:' section.")
        return False, errors

    if "hello" not in jobs:
        errors.append(
            f"Expected a job named 'hello'. Found: {list(jobs.keys())}"
        )
        return False, errors

    hello_job = jobs["hello"]
    if not isinstance(hello_job, dict):
        errors.append("Job 'hello' must be a dictionary.")
        return False, errors

    # --- Check runs-on ---
    runs_on = str(hello_job.get("runs-on", "")).lower()
    if not runs_on:
        errors.append("Job 'hello' is missing 'runs-on:'. Use 'runs-on: ubuntu-latest'.")

    # --- Check steps ---
    steps = hello_job.get("steps", [])
    if not steps or not isinstance(steps, list):
        errors.append("Job 'hello' has no 'steps:' defined.")
        return False, errors

    found_echo = False
    for step in steps:
        if not isinstance(step, dict):
            continue
        run_cmd = str(step.get("run", "")).lower()
        # Accept: echo "Welcome to ZeroOps!", echo 'Welcome to ZeroOps!', echo Welcome...
        if "echo" in run_cmd and "welcome to zeroops" in run_cmd:
            found_echo = True
            break

    if not found_echo:
        errors.append(
            'No step found that echoes "Welcome to ZeroOps!". '
            'Add a step with: run: echo "Welcome to ZeroOps!"'
        )

    return len(errors) == 0, errors


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    """Entry point called by the ZeroOps grader."""

    # 1. Find workflow files on disk first
    files = _find_workflow_files(cwd, filename_hint="hello")
    contents: List[Tuple[str, str]] = []

    if files:
        for f in files:
            try:
                contents.append((f.name, f.read_text()))
            except Exception as e:
                return False, f"Could not read workflow file '{f.name}': {e}"
    elif code.strip():
        contents.append(("workflow.yml", code))
    else:
        return False, (
            "No workflow file found!\n\n"
            "Please create the file '.github/workflows/hello.yml' in your repository.\n"
            "Commit and push it, then sync and submit again."
        )

    all_errors: List[str] = []
    passing_file: str = ""

    for filename, content in contents:
        ok_yaml, data, err_str = _parse_yaml(content)
        if not ok_yaml:
            all_errors.append(f"[{filename}] {err_str}")
            continue

        passed, step_errors = _validate_hello_workflow(data)
        if passed:
            passing_file = filename
            break
        else:
            all_errors.append(f"[{filename}]:\n  ❌ " + "\n  ❌ ".join(step_errors))

    if passing_file:
        return (
            True,
            f"✅ Perfect! Your workflow '{passing_file}' is correctly set up!\n\n"
            "Checks passed:\n"
            "  ✓ Workflow name is 'Hello ZeroOps'\n"
            "  ✓ Trigger is set to 'push'\n"
            "  ✓ Job 'hello' exists\n"
            "  ✓ Echo command prints 'Welcome to ZeroOps!'\n\n"
            "GitHub Actions is ready — let's build something real next! 🚀",
        )

    return (
        False,
        "Workflow validation failed:\n\n" + "\n\n".join(all_errors),
    )
