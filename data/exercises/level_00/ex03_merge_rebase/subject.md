# 🔬 Lab 04: Bringing Branches Together
## "Merge, Conflict, Rebase"

## 🔑 Core Concepts

- Merging one branch into another (`git merge <branch>`)
- Understanding and manually resolving merge conflicts
- Fast-forward merges vs 3-way merge commits
- Rebase (`git rebase <base>`): replaying branch commits linearly onto a new base

## 🧩 Scenario
Two teammates independently renamed the cookbook title on different branches, causing a merge conflict. After resolving the conflict by hand, you will integrate a tips branch using rebase to maintain a clean, linear commit history.

## 🎯 Objective
Resolve a merge conflict manually in `title.txt`, then replay and merge the `feature/tips` branch using rebase and fast-forward.

## 📥 Provided & Initial Setup

- **Work directory:** `~/rendudevops/ex03_merge_rebase/`
- Enter that folder and run the setup script to create the `lab04` practice repository:
  ```bash
  cd ~/rendudevops/ex03_merge_rebase
  git init -b main lab04 && cd lab04
  echo "Pocket Recipes" > title.txt
  git add . && git commit -m "Add title"
  git switch -c feature/italian
  echo "Pocket Recipes - Italian Edition" > title.txt
  git commit -am "Rename title: Italian edition"
  git switch main
  echo "Pocket Recipes - Quick Meals" > title.txt
  git commit -am "Rename title: Quick meals"
  git switch -c feature/tips main~1
  echo "Tip: salt the water" > tips.txt
  git add . && git commit -m "Add tips"
  git switch main
  ```
- **Submission:** This lab is evaluated from your repository in `~/rendudevops/ex03_merge_rebase/lab04/`.

---

## 🛠️ Task List (Split into Parts)

### Part 1 — Merge with Conflict Resolution
1. Verify you are on `main`:
   ```bash
   git branch
   ```
2. Merge the Italian edition branch:
   ```bash
   git merge feature/italian
   ```
   Git will halt and report: `CONFLICT (content): Merge conflict in title.txt`.
3. Open `title.txt`. You will see Git's conflict markers:
   ```
   <<<<<<< HEAD
   Pocket Recipes - Quick Meals
   =======
   Pocket Recipes - Italian Edition
   >>>>>>> feature/italian
   ```
4. Resolve the conflict by editing `title.txt` to contain exactly one single line (remove all marker lines `<<<<<<<`, `=======`, `>>>>>>>`):
   ```
   Pocket Recipes - Italian Quick Meals
   ```
5. Stage the resolved file and complete the merge commit:
   ```bash
   git add title.txt
   git commit --no-edit
   ```

### Part 2 — Rebase & Fast-Forward Integration
1. Switch to the `feature/tips` branch:
   ```bash
   git switch feature/tips
   ```
2. Rebase your tips branch onto `main`:
   ```bash
   git rebase main
   ```
3. Switch back to `main`:
   ```bash
   git switch main
   ```
4. Merge `feature/tips` into `main`:
   ```bash
   git merge feature/tips
   ```
   Notice Git reports **Fast-forward** because the commits now sit in a straight line on top of `main`.
5. Verify with your graph alias:
   ```bash
   git lg
   ```

---

## ⚠️ Constraints

- Resolve the conflict by hand. Do not use automated merge flags (`-X ours`, `-X theirs`).
- `title.txt` must not contain any leftover conflict markers.
- `tips.txt` must be present in the repository alongside `title.txt`.

---

## 🧪 Grading Checklist

The grader evaluates your submission across three distinct parts:

| Part | Description | What the grader checks |
|:---:|:---|:---|
| **Part 1** | Conflict Resolution | `title.txt` exists and contains exactly `Pocket Recipes - Italian Quick Meals` with no conflict markers. |
| **Part 2** | Tips Integration | `tips.txt` exists alongside `title.txt` and contains `Tip: salt the water`. |
| **Part 3** | Clean Working Tree & History | The repository working tree is clean and `feature/tips` is merged into `main`. |

## 🧠 Hints

- If you make a mistake during a merge and want to start over: `git merge --abort`.
- If you make a mistake during a rebase and want to abort: `git rebase --abort`.
- The content between `<<<<<<<` and `=======` is what was on your current branch (`HEAD`); between `=======` and `>>>>>>>` is the incoming branch.
