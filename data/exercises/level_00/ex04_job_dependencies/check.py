"""Validator for Level 00 Exercise 04 — Job Dependencies (needs:)."""

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
        errors.append(f"Missing job 'backend'. Found: {list(jobs.keys())}")

    if "frontend" not in jobs:
        errors.append(f"Missing job 'frontend'. Found: {list(jobs.keys())}")

    if errors:
        return False, errors

    backend_job = jobs["backend"]
    frontend_job = jobs["frontend"]

    # Check that backend does NOT need frontend (reversed order check)
    backend_needs = backend_job.get("needs") if isinstance(backend_job, dict) else None
    if backend_needs:
        needs_str = str(backend_needs).lower()
        if "frontend" in needs_str:
            errors.append("Reversed dependency detected! Job 'backend' should NOT depend on 'frontend'. 'frontend' must depend on 'backend'.")

    # Check that frontend has needs: backend
    frontend_needs = frontend_job.get("needs") if isinstance(frontend_job, dict) else None
    if not frontend_needs:
        errors.append("Job 'frontend' is missing the 'needs: backend' dependency configuration.")
    else:
        needs_list = [frontend_needs] if isinstance(frontend_needs, str) else frontend_needs
        if isinstance(needs_list, list):
            needs_str_list = [str(n).lower() for n in needs_list]
            if "backend" not in needs_str_list:
                errors.append(f"Job 'frontend' needs must include 'backend'. Found: {frontend_needs}")
        else:
            if "backend" not in str(frontend_needs).lower():
                errors.append(f"Job 'frontend' needs must specify 'backend'. Got: {frontend_needs}")

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
        return False, "No workflow file found in 'ex04_job_dependencies/'."

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
            "✅ Excellent work! Your job dependency setup using 'needs:' is correctly configured.\n"
            "Checks passed:\n"
            "  ✓ Top-level 'backend' job\n"
            "  ✓ Top-level 'frontend' job with 'needs: backend'\n"
            "  ✓ Verified execution order: backend -> frontend\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
