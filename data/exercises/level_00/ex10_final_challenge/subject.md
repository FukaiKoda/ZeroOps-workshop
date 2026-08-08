# Exercise 10 — Final Challenge ⭐⭐⭐⭐

## Story
The CTO wants a single, robust production continuous integration pipeline that incorporates almost everything you've learned throughout the workshop into a clean, reproducible workflow.

## Objective
Build an end-to-end production CI pipeline incorporating triggers, checkout, action version pinning, environment variable configuration, dependency installation, testing, and success notification.

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex10_final_challenge/`

Create your workflow file inside this folder (e.g. `ex10_final_challenge/workflow.yml`).

## Pipeline Specification

Your production workflow must satisfy the following sequence and rules:

1. **Triggers**: Trigger on `push` (filtered to `main` branch) and `pull_request` events.
2. **Checkout**: Checkout repository code using `actions/checkout@v4`.
3. **Setup Python**: Install Python using pinned `actions/setup-python@v5` with `python-version: '3.11'`.
4. **Environment Configuration**: Set `env: PROJECT_NAME: "ZeroOps Production"` (or your custom project name) and print it.
5. **Install Dependencies**: Execute step running `pip install -r requirements.txt` (or `pip install pytest`).
6. **Run Tests**: Execute step running `pytest` (or `python -m pytest`).
7. **Success Notification**: Print a final pipeline success message.


