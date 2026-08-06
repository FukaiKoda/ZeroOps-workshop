# Exercise 01 — Build Pipeline ⭐⭐

## Story
The development team wants every commit to be validated before merging. To enforce quality standards across the project, you have been tasked with creating the team's first **GitHub Actions** CI pipeline.

## Objective
Build a continuous integration workflow using GitHub Actions that checks out the repository and performs basic system environment checks.

## Tasks
Create a workflow file in your GitHub repository at `.github/workflows/build.yml` (or `.github/workflows/ci.yml`).

Your pipeline must perform the following sequence:

1. **Checkout Code**: Uses the official `actions/checkout` action.
2. **Print Python Version**: Executes a command to print Python version (`python --version` or `python3 --version`).
3. **Print Current Directory**: Executes a command to display working directory (`pwd`).
4. **List Repository Files**: Executes a command to list all repository files (`ls -la` or `ls`).

## What You Will Learn
- GitHub Actions workflow syntax (`name`, `on`, `jobs`, `steps`)
- Using official marketplace actions (`uses: actions/checkout@v4`)
- Executing shell instructions in CI steps (`run: ...`)

## Expected Workflow Location
```text
.github/workflows/build.yml
```

## Workflow Example
```yaml
name: Build Pipeline

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Print Python Version
        run: python --version

      - name: Print Current Directory
        run: pwd

      - name: List Repository Files
        run: ls -la
```

## How to Submit
1. In your local repository clone, create `.github/workflows/build.yml` with your workflow definition.
2. Commit and push your changes to GitHub:
   ```bash
   git add .github/workflows/build.yml
   git commit -m "feat: add GitHub Actions build pipeline"
   git push origin main
   ```
3. Open the ZeroOps TUI client, click **🔄 Sync Repository** to detect your commit, and then click **Submit**!
