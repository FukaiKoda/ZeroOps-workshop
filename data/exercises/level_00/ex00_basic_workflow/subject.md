# 🔬 Lab 01: The Careful Commit
## "Look Before You Commit"

## 🔑 Core Concepts

- The three Git areas: working directory → staging area (index) → repository history
- Inspecting changes with `git status` and `git diff` before committing
- Staging specific files individually with `git add <file>` instead of bulk-adding

## 🧩 Scenario
You have joined the "Pocket Recipes" team. The team lead noticed your commits are cluttered because everything was added at once with `git add .`. Your first task is to build a clean history where each commit represents a single focused change.

## 🎯 Objective
Create a new Git repository with focused commits, staging and committing files one at a time.

## 📥 Provided & Work Directory

- **Work directory:** `~/rendudevops/ex00_basic_workflow/`
- Inside that directory, create or enter the repository folder: `pocket-recipes/`
  ```bash
  mkdir -p ~/rendudevops/ex00_basic_workflow/pocket-recipes
  cd ~/rendudevops/ex00_basic_workflow/pocket-recipes
  git init -b main
  ```
- **Submission:** This lab is evaluated from your local files in `~/rendudevops/ex00_basic_workflow/`.

---

## 🛠️ Task List (Split into Parts)

### Part 1 — Initial Recipe (`pasta.txt`)
1. Create `pasta.txt` with the following initial content:
   ```bash
   echo "Pasta: boil water, add pasta, cook 10 minutes" > pasta.txt
   ```
2. Create `salad.txt` for the next recipe:
   ```bash
   echo "Salad: chop vegetables, add oil" > salad.txt
   ```
3. Run `git status` — both files should show under **Untracked files**.
4. Stage **only** `pasta.txt`:
   ```bash
   git add pasta.txt
   ```
5. Commit `pasta.txt`:
   ```bash
   git commit -m "Add pasta recipe"
   ```

### Part 2 — Add Serving Tip to `pasta.txt`
1. Append the serving tip to `pasta.txt`:
   ```bash
   echo "Serve hot" >> pasta.txt
   ```
2. Check your changes with `git diff` to verify only the new line was added.
3. Stage and commit the serving tip:
   ```bash
   git add pasta.txt
   git commit -m "Add serving tip"
   ```

### Part 3 — Manage `salad.txt` & Staging Practice
1. Practice unstaging: stage `salad.txt` by accident:
   ```bash
   git add salad.txt
   ```
2. Unstage it using `git restore --staged salad.txt` (or commit it if you complete the bonus).
3. Ensure `salad.txt` remains present in the repository alongside `pasta.txt`.
4. Review your commit log with `git log --oneline`.

### ⭐ Bonus (Optional)
Commit `salad.txt` with a deliberate typo (`Add salda recipe`), then amend the commit message to `Add salad recipe` using `git commit --amend -m "Add salad recipe"`.

---

## ⚠️ Constraints

- Do not use `git add .` or `git add -A`. Always stage specific files.
- Keep `pasta.txt` and `salad.txt` in the same directory.

---

## 🧪 Grading Checklist

The grader evaluates your submission in three distinct parts:

| Part | Description | What the grader checks |
|:---:|:---|:---|
| **Part 1** | Initial Recipe | `pasta.txt` exists and contains `Pasta: boil water, add pasta, cook 10 minutes`. |
| **Part 2** | Serving Tip | `pasta.txt` contains `Serve hot` (both lines must be present). |
| **Part 3** | Secondary Recipe | `salad.txt` exists alongside `pasta.txt` and contains `Salad: chop vegetables, add oil`. |

## 🧠 Hints

- `git status` is safe to run anytime to inspect your index and working tree.
- `git diff` shows unstaged changes; `git diff --staged` shows what will be in the next commit.
