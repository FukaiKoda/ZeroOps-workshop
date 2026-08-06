# Exercise 08 — CI Detective ⭐⭐⭐

## Story
Real CI engineers spend a significant amount of time inspecting raw build logs to diagnose pipeline failures. Read three real build failure logs, determine the root cause for each, and record your diagnostic choices.

## Objective
Analyze CI failure logs and diagnose missing pipeline prerequisites (`actions/setup-python`, `actions/checkout`, or working directory alignment).

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex08_ci_detective/`

Create an `answers.json` file inside this directory containing your diagnostic choices.

---

## Log Scenarios

### Scenario A
```text
Run python app.py
python: command not found
Error: Process completed with exit code 127.
```
**Options for Scenario A:**
- `1`: The Python script has a syntax error.
- `2`: `actions/setup-python` is missing from the workflow.
- `3`: The runner operating system is down.
- `4`: `actions/checkout` was not called.

### Scenario B
```text
Run pytest tests/
pytest: error: No such file or directory: tests/
Error: Process completed with exit code 2.
```
**Options for Scenario B:**
- `1`: Pytest is incompatible with Ubuntu.
- `2`: The API key secret is missing.
- `3`: `actions/checkout` is missing, so repository files were not fetched to the runner.
- `4`: Python version 3.11 is not supported.

### Scenario C
```text
Run pip install -r requirements.txt
ERROR: Could not open requirements.txt: No such file or directory
Error: Process completed with exit code 1.
```
**Options for Scenario C:**
- `1`: Wrong working directory or repository structure mismatch.
- `2`: GitHub API rate limit exceeded.
- `3`: `actions/checkout` requires a personal access token.
- `4`: Python is not installed.

---

## Tasks

Create `ex08_ci_detective/answers.json` with the option numbers (1-4) selected for each scenario:

```json
{
  "scenario_a": 2,
  "scenario_b": 3,
  "scenario_c": 1
}
```
