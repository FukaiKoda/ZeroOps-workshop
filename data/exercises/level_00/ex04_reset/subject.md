# 🔬 Lab 05: Time Travel
## "Undoing Commits (and Getting Them Back)"

## 🔑 Core Concepts

- The three modes of `git reset`:
  - `--soft`: Moves HEAD pointer back; keeps your changes **staged** in the index.
  - `--mixed` (default): Moves HEAD back; unstages changes but keeps them in your **working directory**.
  - `--hard`: Moves HEAD back and **discards** changes from both index and working tree.
- `git reflog`: Git's local flight recorder that tracks every movement of HEAD, serving as your safety net to recover seemingly lost commits.

## 🧩 Scenario
A teammate committed work prematurely and wants you to test undoing commits using different reset strategies. During the `--hard` reset, the latest progress is wiped out, so you will use `git reflog` to resurrect the commit and restore the full history.

## 🎯 Objective
Experience `--soft`, `--mixed`, and `--hard` resets, and use `git reflog` to safely recover from a hard reset.

## 📥 Provided & Initial Setup

- **Work directory:** `~/rendudevops/ex04_reset/`
- Enter that folder and run the setup script to initialize the `lab05` practice repository:
  ```bash
  cd ~/rendudevops/ex04_reset
  git init -b main lab05 && cd lab05
  for i in 1 2 3; do echo "step $i" >> progress.txt; git add . ; git commit -m "Step $i"; done
  ```
- **Submission:** This lab is evaluated from your repository in `~/rendudevops/ex04_reset/lab05/`.

---

## 🛠️ Task List (Split into Parts)

### Part 1 — Soft Reset (`--soft`)
1. View initial state (3 commits, 3 lines):
   ```bash
   git lg
   cat progress.txt
   ```
2. Undo the last commit while keeping changes staged:
   ```bash
   git reset --soft HEAD~1
   ```
3. Run `git status` — notice `progress.txt` is already staged (green).
4. Recommit it:
   ```bash
   git commit -m "Step 3 again"
   ```

### Part 2 — Mixed Reset (`--mixed`)
1. Undo the last commit while unstaging changes:
   ```bash
   git reset --mixed HEAD~1
   ```
2. Run `git status` — `progress.txt` is modified but **not staged** (red).
3. Stage and recommit:
   ```bash
   git commit -am "Step 3 again"
   ```

### Part 3 — Hard Reset (`--hard`) and Reflog Recovery
1. Run a hard reset to discard the commit and its changes:
   ```bash
   git reset --hard HEAD~1
   ```
2. Check `progress.txt`:
   ```bash
   cat progress.txt
   ```
   Notice that `step 3` is gone!
3. Open the reflog to find the commit SHA before the reset:
   ```bash
   git reflog
   ```
   Look for the entry right before the reset (e.g. `HEAD@{1}`).
4. Recover the lost commit:
   ```bash
   git reset --hard 'HEAD@{1}'
   ```
5. Confirm that `progress.txt` now contains all three lines:
   ```bash
   cat progress.txt
   # Should output:
   # step 1
   # step 2
   # step 3
   ```

### ⭐ Bonus (Optional: Revert)
Run `git revert HEAD --no-edit` and observe how `revert` differs from `reset`: revert creates a *new* inverse commit rather than rewriting history.

---

## ⚠️ Constraints

- Perform all reset commands inside the `lab05/` repository.
- After recovery, `progress.txt` must contain all 3 steps (`step 1`, `step 2`, `step 3`).

---

## 🧪 Grading Checklist

The grader evaluates your submission across three distinct parts:

| Part | Description | What the grader checks |
|:---:|:---|:---|
| **Part 1** | File Presence | `progress.txt` is present in `lab05/` or the exercise directory. |
| **Part 2** | Restored Steps | `progress.txt` contains all three steps (`step 1`, `step 2`, `step 3`). |
| **Part 3** | Commit Recovery | History has all 3 steps restored via reflog. |

## 🧠 Hints

- Quick memory rule:
  - **soft** keeps changes in the index (staged)
  - **mixed** keeps changes in the working tree (unstaged)
  - **hard** discards changes
- `git reflog` records local HEAD movements for about 30–90 days, giving you ample time to rescue any committed work.
