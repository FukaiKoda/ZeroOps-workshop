# Exercise 00 — Hello Workflow ⭐

## Story

The engineering team wants to verify that **GitHub Actions** is correctly set up in the repository.
Before building complex pipelines, you need to confirm the system works.

Your mission: create your first workflow and make it say hello.

---

## Objective

When code is pushed to the repository, GitHub Actions must execute a workflow that prints a greeting message.

---

## Tasks

Create the file `.github/workflows/hello.yml` in your repository with the following requirements:

| Requirement | Value |
|-------------|-------|
| Workflow name | `Hello ZeroOps` |
| Trigger | `push` |
| Job name | `hello` |
| Runner | `ubuntu-latest` |
| Step output | Print `Welcome to ZeroOps!` |

---

## What You Will Learn

- The basic structure of a GitHub Actions workflow file
- How to use the `on:` trigger to run on `push`
- How to define a `job` with `runs-on`
- How to execute a shell command with `run:`

---

## Expected File Location

```
.github/workflows/hello.yml
```

---

## Example Solution

```yaml
name: Hello ZeroOps

on: push

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - name: Say Hello
        run: echo "Welcome to ZeroOps!"
```

---

## How to Submit

1. In your repository, create the file `.github/workflows/hello.yml`.
2. Commit and push it to GitHub:
   ```bash
   git add .github/workflows/hello.yml
   git commit -m "feat: add Hello ZeroOps workflow"
   git push origin main
   ```
3. In the ZeroOps TUI, click **🔄 Sync Repository** then **Submit**. The validator will check your workflow automatically.
