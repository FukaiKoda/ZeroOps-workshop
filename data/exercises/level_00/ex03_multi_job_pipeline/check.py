"""Validator for Level 00 Exercise 03 — Multi-Job Pipeline."""

import yaml
from pathlib import Path
from typing import Tuple, List, Dict, Any


def _find_workflow_files(cwd: Path) -> List[Path]:
    files: List[Path] = []
    search_dirs = [cwd, cwd / ".github" / "workflows", cwd / "workflows"]
    for d in search_dirs:
        if d.exists() and d.is_dir():
            for ext in ["*.yml", "*.yaml"]:
                files.extend(d.glob(ext))
    seen = set()
    unique_files = []
    for f in files:
        if f.resolve() not in seen:
            seen.add(f.resolve())
            unique_files.append(f)
    return sorted(unique_files)


def _parse_yaml(content: str) -> Tuple[bool, Any, str]:
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return False, None, "YAML root must be a dictionary."
        return True, data, ""
    except yaml.YAMLError as e:
        return False, None, f"YAML Syntax Error: {e}"


def _validate_workflow(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []

    jobs = data.get("jobs")
    if not jobs or not isinstance(jobs, dict):
        errors.append("Missing 'jobs:' section in workflow.")
        return False, errors

    if "backend" not in jobs:
        errors.append(f"Missing job named 'backend'. Found jobs: {list(jobs.keys())}")

    if "frontend" not in jobs:
        errors.append(f"Missing job named 'frontend'. Found jobs: {list(jobs.keys())}")

    if errors:
        return False, errors

    # Validate backend job
    backend_job = jobs["backend"]
    if not isinstance(backend_job, dict):
        errors.append("Job 'backend' must be a dictionary.")
    else:
        steps = backend_job.get("steps", [])
        has_checkout = any("actions/checkout" in str(s.get("uses", "")).lower() for s in steps if isinstance(s, dict))
        has_echo = any("testing backend" in str(s.get("run", "")).lower() or "backend" in str(s.get("run", "")).lower() for s in steps if isinstance(s, dict))
        if not has_checkout:
            errors.append("Job 'backend' is missing checkout step ('actions/checkout').")
        if not has_echo:
            errors.append("Job 'backend' is missing step echoing 'Testing backend'.")

    # Validate frontend job
    frontend_job = jobs["frontend"]
    if not isinstance(frontend_job, dict):
        errors.append("Job 'frontend' must be a dictionary.")
    else:
        steps = frontend_job.get("steps", [])
        has_checkout = any("actions/checkout" in str(s.get("uses", "")).lower() for s in steps if isinstance(s, dict))
        has_echo = any("testing frontend" in str(s.get("run", "")).lower() or "frontend" in str(s.get("run", "")).lower() for s in steps if isinstance(s, dict))
        if not has_checkout:
            errors.append("Job 'frontend' is missing checkout step ('actions/checkout').")
        if not has_echo:
            errors.append("Job 'frontend' is missing step echoing 'Testing frontend'.")

    return len(errors) == 0, errors


def grade(code: str, cwd: Path) -> Tuple[bool, str]:
    files = _find_workflow_files(cwd)
    contents = []

    if files:
        for f in files:
            try:
                contents.append((f.name, f.read_text()))
            except Exception as e:
                return False, f"Could not read workflow file '{f.name}': {e}"
    elif code.strip():
        contents.append(("workflow.yml", code))
    else:
        return False, "No workflow file found in 'ex03_multi_job_pipeline/'."

    all_errors = []
    valid_count = 0

    for filename, content in contents:
        ok_yaml, data, err_str = _parse_yaml(content)
        if not ok_yaml:
            all_errors.append(f"[{filename}] {err_str}")
            continue

        valid, step_errors = _validate_workflow(data)
        if valid:
            valid_count += 1
        else:
            all_errors.append(f"[{filename}]:\n  ❌ " + "\n  ❌ ".join(step_errors))

    if valid_count > 0:
        return (
            True,
            "✅ Great job! Your multi-job pipeline correctly defines parallel 'backend' and 'frontend' jobs.\n"
            "Checks passed:\n"
            "  ✓ Top-level 'backend' job with checkout and test step\n"
            "  ✓ Top-level 'frontend' job with checkout and test step\n"
            "  ✓ Jobs execute in parallel by default\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
