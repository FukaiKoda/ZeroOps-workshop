# 🔬 Lab 03: Parallel Universes
## "Work on Two Things Without Breaking Either"

## 🔑 Core Concepts

- A branch is a movable label on a commit
- Creating and switching branches with `git switch`
- Seeing branches diverge with `git lg`

## 🧩 Scenario
The team wants a new dessert section, but the main recipes must stay untouched until it's ready. You'll build the dessert on its own branch.

## 🎯 Objective
Create a branch, commit on it, and see how `main` and your branch live side by side.

## 📥 Provided

- The `pocket-recipes` repository from Lab 01, with a clean working tree.

## 🛠️ Task List

- Run `git branch` to see where you are (the current branch has a `*`).
- Create and switch to a new branch: `git switch -c feature/dessert`.
- Create `dessert.txt` (`echo "Tiramisu" > dessert.txt`), then stage and commit it.
- Go back with `git switch main` and run `ls`. What happened to `dessert.txt`? Switch back to `feature/dessert` and look again.
- On `main`, add a line to `pasta.txt` and commit it.
- Run `git lg` and spot the two branches going in different directions.
- ⭐ **Bonus (stash):** edit `pasta.txt` on `main` without committing, then try `git switch feature/dessert`. If Git refuses, run `git stash`, switch, switch back and run `git stash pop` to get your edit back.

## ⚠️ Constraints

- Do not merge anything yet. That's the next lab.

## 🧪 Validation

- `git branch` lists `main` and `feature/dessert`.
- On `main`, the file `dessert.txt` does not exist.

## 🧠 Hints

- `git switch -c <name>` creates the branch and moves to it in one step.
- Git sometimes refuses to switch when you have uncommitted changes. That's protection, not a bug.

---
