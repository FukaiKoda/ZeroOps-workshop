# 🔬 Lab 01: The Careful Commit
## "Look Before You Commit"

## 🔑 Core Concepts

- The three areas: working directory → staging area → repository
- Reading `git status` and `git diff` before committing
- Staging specific files instead of everything

## 🧩 Scenario
You've joined the "Pocket Recipes" team. The lead noticed your commits are huge because everything goes in with `git add .`. Your first task is to build a small, clean history where each commit holds exactly one change.

## 🎯 Objective
Create a new repository with two focused commits, staging files one at a time.

## 📥 Provided

- A terminal with Git installed (`git --version` works).

## 🛠️ Task List

- Create a folder called `pocket-recipes`, enter it and run `git init`.
- Create two files:
  - `echo "Pasta: boil water, add pasta, cook 10 minutes" > pasta.txt`
  - `echo "Salad: chop vegetables, add oil" > salad.txt`
- Run `git status`. Both files should be listed as untracked.
- Stage **only** `pasta.txt` with `git add pasta.txt`. Run `git status` again and notice the two sections. Commit with `git commit -m "Add pasta recipe"`.
- Add one more line to `pasta.txt` (`echo "Serve hot" >> pasta.txt`). Run `git diff` to see the change, then `git add pasta.txt`, then `git diff --staged`. Commit it with `Add serving tip`.
- Stage `salad.txt` by accident (`git add salad.txt`), then unstage it with `git restore --staged salad.txt`.
- Run `git log --oneline` to see your history.
- ⭐ **Bonus:** commit `salad.txt` with the message `Add salda recipe` (typo on purpose) and fix it using `git commit --amend`.

## ⚠️ Constraints

- Do not use `git add .` in this lab.

## 🧪 Validation

- `git log --oneline` shows 2 commits (3 if you did the bonus).
- `git status` shows `salad.txt` as untracked (or clean, if you did the bonus).

## 🧠 Hints

- `git status` is always safe. When in doubt, run it.
- `git diff` shows changes that are **not staged yet**, and `git diff --staged` shows what **will go into the next commit**.

---
