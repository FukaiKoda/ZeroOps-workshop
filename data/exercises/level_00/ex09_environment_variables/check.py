"""Validator for Level 00 Exercise 09 — Environment Variables."""

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

    # Check top-level or job-level env
    top_env = data.get("env") or {}
    job_envs = []
    jobs = data.get("jobs", {})
    if isinstance(jobs, dict):
        for job_cfg in jobs.values():
            if isinstance(job_cfg, dict) and "env" in job_cfg:
                job_envs.append(job_cfg.get("env"))

    all_env_keys = set(top_env.keys() if isinstance(top_env, dict) else [])
    for je in job_envs:
        if isinstance(je, dict):
            all_env_keys.update(je.keys())

    if "PROJECT_NAME" not in all_env_keys:
        errors.append("Missing environment variable 'PROJECT_NAME' in 'env:' block.")

    if "AUTHOR" not in all_env_keys:
        errors.append("Missing environment variable 'AUTHOR' in 'env:' block.")

    # Check step run command for shell variable usage ($PROJECT_NAME and $AUTHOR)
    all_steps: List[Dict[str, Any]] = []
    if isinstance(jobs, dict):
        for job_cfg in jobs.values():
            if isinstance(job_cfg, dict):
                steps = job_cfg.get("steps", [])
                if isinstance(steps, list):
                    all_steps.extend([s for s in steps if isinstance(s, dict)])

    found_shell_echo = False
    for step in all_steps:
        run_cmd = str(step.get("run", ""))
        if "PROJECT_NAME" in run_cmd and "AUTHOR" in run_cmd:
            if "$" in run_cmd:
                found_shell_echo = True

    if not found_shell_echo:
        errors.append("Missing step executing echo command referencing shell variables '$PROJECT_NAME' and '$AUTHOR'.")

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
        return False, "No workflow file found in 'ex09_environment_variables/'."

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
            "✅ Excellent work! Your workflow correctly configures environment variables in env: and uses shell interpolation.\n"
            "Checks passed:\n"
            "  ✓ Defined env: block with PROJECT_NAME and AUTHOR\n"
            "  ✓ Printed values using shell interpolation ($PROJECT_NAME and $AUTHOR)\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
