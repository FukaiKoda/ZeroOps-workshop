# 🔬 Lab 07: The Bouncer
## "Keeping Junk and Secrets Out of Git"

## 🔑 Core Concepts

- `.gitignore` pattern syntax (wildcards `*.log`, directory slashes `build/`, explicit files `.env`)
- `.gitignore` only applies to **untracked** files — once a file is tracked, adding it to `.gitignore` does not ignore future changes
- Untracking an existing file without deleting it from disk using `git rm --cached <file>`

## 🧩 Scenario
A teammate accidentally committed a `.env` file containing an API key on day one. Now, transient log files and compiled build artifacts continuously clutter `git status`. You need to configure `.gitignore` rules and safely untrack the `.env` secret while leaving the local copy intact on disk.

## 🎯 Objective
Configure `.gitignore` rules to ignore build output and logs, and stop Git from tracking `.env` while preserving the file locally.

## 📥 Provided & Initial Setup

- **Work directory:** `~/rendudevops/ex06_gitignore/`
- Enter that folder and run the setup script to initialize the `lab07` repository:
  ```bash
  cd ~/rendudevops/ex06_gitignore
  git init -b main lab07 && cd lab07
  echo "print('hello')" > app.py
  echo "API_KEY=super-secret-123" > .env
  git add . && git commit -m "Initial commit"
  echo "debug line" > debug.log
  mkdir build && echo "compiled" > build/output.bin
  ```
- **Submission:** This lab is evaluated from your repository in `~/rendudevops/ex06_gitignore/lab07/`.

---

## 🛠️ Task List (Split into Parts)

### Part 1 — Create `.gitignore` Rules
1. Inspect the untracked files:
   ```bash
   git status
   # debug.log and build/ appear under Untracked files
   ```
2. Create `.gitignore` with the three required rules:
   ```bash
   printf '*.log\nbuild/\n.env\n' > .gitignore
   ```
3. Run `git status` again. Notice that `debug.log` and `build/` have disappeared.
4. Verify ignore matching with Git's diagnostic tool:
   ```bash
   git check-ignore -v debug.log
   ```

### Part 2 — Untrack `.env` Without Deleting It
1. Modify `.env` to test tracking behavior:
   ```bash
   echo "API_KEY=new-test-secret" > .env
   ```
2. Run `git status`. Notice `.env` still shows as **modified** even though it is listed in `.gitignore` (because Git already tracks it).
3. Stop tracking `.env` from the repository while keeping it on your local disk:
   ```bash
   git rm --cached .env
   ```
4. Commit the removal:
   ```bash
   git commit -m "Stop tracking .env"
   ```
5. Confirm `.env` still exists on disk:
   ```bash
   ls -la .env
   cat .env
   ```

### Part 3 — Commit `.gitignore` and Verify Clean State
1. Stage and commit `.gitignore`:
   ```bash
   git add .gitignore
   git commit -m "Add .gitignore"
   ```
2. Verify which files Git currently tracks:
   ```bash
   git ls-files
   # Should list ONLY: .gitignore and app.py
   ```
3. Verify directory contents:
   ```bash
   ls
   # app.py, debug.log, build/, .env, and .gitignore are all physically on disk
   ```

---

## ⚠️ Constraints

- Do not physically delete `.env` from disk (do not use `rm .env` or plain `git rm .env`).
- `.gitignore` must contain rules for `*.log`, `build/`, and `.env`.
- `app.py` must remain tracked.

---

## 🧪 Grading Checklist

The grader evaluates your submission across three distinct parts:

| Part | Description | What the grader checks |
|:---:|:---|:---|
| **Part 1** | Ignore Rules | `.gitignore` exists and contains patterns: `*.log`, `build/`, and `.env`. |
| **Part 2** | Untracked Secret | `.env` exists on disk but is no longer tracked by Git. |
| **Part 3** | Application Preserved | `app.py` remains tracked and present in the repository. |

## 🧠 Hints

- A trailing slash like `build/` restricts the ignore rule strictly to directories.
- `git rm --cached` removes files from the staging index while leaving the working copy untouched.
- In production, removing a tracked secret from Git does not purge it from historical commits; leaked credentials must always be revoked immediately.
