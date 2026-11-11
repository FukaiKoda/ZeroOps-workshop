# 🔬 Lab 03: Parallel Universes
## "Work on Two Things Without Breaking Either"

## 🔑 Core Concepts

- A branch is a movable, lightweight pointer to a specific commit
- Creating and switching branches safely using `git switch`
- Observing branch divergence where independent lines of work coexist
- Progressive development and checkpoint validation

## 🧩 Scenario
The team wants to introduce a dessert section to Pocket Recipes, but the `main` recipe line must stay stable and untouched while dessert recipes are developed. You will build the dessert feature on its own isolated branch, submit to verify your progress, and then make an independent update on `main`.

## 🎯 Objective
Create a feature branch, commit a new recipe to it, verify your checkpoint, switch back to `main` to make an independent commit, and observe the two branches diverge.

## 📥 Provided & Work Directory

- The `pocket-recipes` repository from Lab 01 (with a clean working tree).
- **Work directory:** `~/rendudevops/ex02_branching/pocket-recipes/`
  ```bash
  cd ~/rendudevops/ex02_branching/pocket-recipes
  cp -r ~/rendudevops/ex00_basic_workflow/pocket-recipes/ ~/rendudevops/ex02_branching/
  ```
- **Submission:** This lab is evaluated from your repository in `~/rendudevops/ex02_branching/`. You can submit at each checkpoint to verify your progress!

---

## 🛠️ Task List (Split into Progressive Parts)

### Part 1 — Create and Commit on `feature/dessert`
1. Check your current active branch:
   ```bash
   git branch
   ```
2. Create and switch to a new branch called `feature/dessert`:
   ```bash
   git switch -c feature/dessert
   ```
3. Create `dessert.txt` with the following content:
   ```bash
   echo "Tiramisu" > dessert.txt
   ```
4. Stage and commit your dessert recipe:
   ```bash
   git add dessert.txt
   git commit -m "Add dessert"
   ```

> 💡 **Checkpoint 1 (Submit & Verify Progress):**
> You can click **Submit** right now in the dashboard! The grader will verify that Part 1 and Part 2 are complete, confirm your dessert recipe, and guide you on what to do next for Part 3.

---

### Part 2 — Switch to `main` and Make an Independent Commit
1. Switch back to the `main` branch:
   ```bash
   git switch main
   ```
2. Verify that `dessert.txt` is **not present** on `main` (run `ls` — notice that `main` is untouched!).
3. Update `pasta.txt` by appending `Add basil`:
   ```bash
   echo "Add basil" >> pasta.txt
   ```
4. Commit the change on `main`:
   ```bash
   git commit -am "Add basil to pasta"
   ```

---

### Part 3 — Inspect Divergence & Final Submission
1. Run your log graph alias (or full command):
   ```bash
   git lg
   # or: git log --oneline --graph --all --decorate
   ```
2. Notice how history splits into two separate paths from the common ancestor commit.
3. Click **Submit** in the dashboard to complete the lab!

---

### ⭐ Bonus (Optional: Git Stash)
1. On `main`, edit `pasta.txt` without committing: `echo "Extra garlic" >> pasta.txt`.
2. Try switching with `git switch feature/dessert` — Git prevents overwriting your uncommitted work.
3. Save your work into the stash: `git stash`.
4. Now switch freely to `feature/dessert`, then back to `main`.
5. Restore your uncommitted edit with `git stash pop`.

---

## ⚠️ Constraints

- Do not merge `feature/dessert` into `main` yet (merging is covered in Lab 04).
- `dessert.txt` must contain exactly `Tiramisu`.

---

## 🧪 Grading Checklist

The grader evaluates your submission progressively across three parts:

| Part | Description | What the grader checks | Progressive Feedback |
|:---:|:---|:---|:---|
| **Part 1** | Branch Existence | Branch `feature/dessert` exists in the repository. | If missing, shows command to create branch. |
| **Part 2** | Dessert Recipe | `dessert.txt` is committed on `feature/dessert` and contains `Tiramisu`. | Confirms checkpoint and displays next instructions. |
| **Part 3** | Main Divergence | `main` has its independent update (`Add basil` in `pasta.txt`). | Validates full divergence and passes the lab. |

## 🧠 Hints

- `git switch -c <name>` combines creating a new branch and switching to it in a single step.
- Branches in Git are just lightweight pointers to commits. Switching branches updates your working directory to match the commit of that branch.
