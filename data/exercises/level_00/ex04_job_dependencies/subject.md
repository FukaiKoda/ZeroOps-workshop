# Exercise 04 — Job Dependencies (needs:) ⭐⭐⭐

## Story
The frontend application depends on API contracts established by the backend. Therefore, the Frontend build job must not execute until Backend tests pass successfully.

## Objective
Learn how to use the `needs:` dependency keyword to control job execution order and turn parallel jobs into a sequential pipeline (test → build → deploy).

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex04_job_dependencies/`

Create your workflow file inside this folder (e.g. `ex04_job_dependencies/workflow.yml`).

## Tasks

Reuse Exercise 03's `backend` and `frontend` jobs:

1. **Job `backend`**:
   - Runs tests and echoes `"Backend tests passing"`.
2. **Job `frontend`**:
   - Add `needs: backend` dependency so it waits for the `backend` job to succeed before starting.
   - Echoes `"Building frontend after backend success"`.

---

> 💡 **Key Concept: Controlling Execution Order with `needs:`**
> By default, jobs in GitHub Actions run concurrently. Adding `needs: <job_id>` forces a job to wait for the specified job(s) to complete successfully before starting.

---

## Example Workflow Structure

```yaml
name: Job Dependencies
on: push

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Backend Tests
        run: echo "Backend tests passing"

  frontend:
    needs: backend
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build Frontend
        run: echo "Building frontend after backend success"
```
