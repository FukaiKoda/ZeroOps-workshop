"""Validator for Level 00 Exercise 09 — Secrets."""

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


def _validate_workflow(data: Dict[str, Any], raw_yaml: str) -> Tuple[bool, List[str]]:
    errors = []
    raw_lower = raw_yaml.lower()

    # 1. Check for hardcoded API keys
    if "api_key=12345" in raw_lower or "api_key: 12345" in raw_lower or "api_key: \"12345\"" in raw_lower:
        errors.append("Hardcoded credential detected ('API_KEY=12345')! Always use '${{ secrets.API_KEY }}'.")

    # 2. Check secrets.API_KEY reference
    if "secrets.api_key" not in raw_lower:
        errors.append("Missing secret reference '${{ secrets.API_KEY }}' in workflow.")

    # 3. Check steps for safe secret debugging (length check)
    jobs = data.get("jobs", {})
    all_steps: List[Dict[str, Any]] = []
    if isinstance(jobs, dict):
        for j_cfg in jobs.values():
            if isinstance(j_cfg, dict):
                steps = j_cfg.get("steps", [])
                if isinstance(steps, list):
                    all_steps.extend([s for s in steps if isinstance(s, dict)])

    found_secret_env = False
    found_safe_length_print = False

    for step in all_steps:
        step_env = step.get("env", {})
        if isinstance(step_env, dict) and any("api_key" in str(k).lower() for k in step_env.keys()):
            val_str = str(step_env.get("API_KEY") or step_env.get("api_key") or "")
            if "secrets.api_key" in val_str.lower():
                found_secret_env = True

        run_cmd = str(step.get("run", ""))
        if "${#api_key}" in run_cmd.lower() or "${#api_key}" in run_cmd.lower():
            found_safe_length_print = True

    if "secrets.api_key" in raw_lower:
        found_secret_env = True

    if "${#api_key}" in raw_lower:
        found_safe_length_print = True

    if not found_secret_env:
        errors.append("Missing env: block mapping 'API_KEY: ${{ secrets.API_KEY }}'.")

    if not found_safe_length_print:
        errors.append("Missing safe secret length print 'echo \"Key length: ${#API_KEY}\"'. Do NOT print raw secret values directly!")

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
        return False, "No workflow file found in 'ex09_secrets/'."

    all_errors = []
    valid_count = 0

    for filename, content in contents:
        ok_yaml, data, err_str = _parse_yaml(content)
        if not ok_yaml:
            all_errors.append(f"[{filename}] {err_str}")
            continue

        valid, step_errors = _validate_workflow(data, content)
        if valid:
            valid_count += 1
        else:
            all_errors.append(f"[{filename}]:\n  ❌ " + "\n  ❌ ".join(step_errors))

    if valid_count > 0:
        return (
            True,
            "✅ Excellent security practices! Your workflow safely injects and handles secrets.\n"
            "Checks passed:\n"
            "  ✓ Mapped secret via env: API_KEY: ${{ secrets.API_KEY }}\n"
            "  ✓ Practiced safe secret debugging by printing key length (${#API_KEY})\n"
            "  ✓ Zero hardcoded credential strings detected\n"
        )

    return False, "Validation failed:\n" + "\n".join(all_errors)
