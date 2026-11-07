# 🔬 Lab 04: Bringing Branches Together
## "Merge, Conflict, Rebase"

## 🔑 Core Concepts

- Merging one branch into another
- What a merge conflict is and how to resolve it
- Rebase: replaying your commits on top of another branch for a straight history

## 🧩 Scenario
Two teammates renamed the book title at the same time and each thinks theirs is right. After you resolve that, you'll tidy up a small branch with rebase so the history stays a straight line.

## 🎯 Objective
Resolve one merge conflict by hand, then integrate a second branch using rebase.

## 📥 Provided

- A fresh practice repo. Create it with this script:

```bash
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

## 🛠️ Task List

**Part A: Merge with a conflict**

- Run `git lg`. You'll see several branches that went in different directions.
- On `main`, run `git merge feature/italian`. Git reports a conflict.
- Open `title.txt` and look at the `<<<<<<<`, `=======` and `>>>>>>>` lines. Edit the file so it contains one single line: `Pocket Recipes - Italian Quick Meals` (remove all marker lines).
- Save, then run `git add title.txt` and `git commit` (keep the default message).

**Part B: Rebase (short)**

- Run `git switch feature/tips`, then `git rebase main`.
- Run `git lg` and notice that the `Add tips` commit now sits on top of `main` in a straight line.
- Go back to `main` and run `git merge feature/tips`. Git says **Fast-forward**, with no merge commit.

## ⚠️ Constraints

- Resolve the conflict by hand. No automatic options.

## 🧪 Validation

- `git status` says the working tree is clean.
- `cat title.txt` shows your single resolved line, with no `<<<<<<<` markers.
- `git lg` shows one merge commit (Part A) and a straight line for `Add tips`.

## 🧠 Hints

- Stuck in the conflict and want out? `git merge --abort` returns you to before the merge.
- The part above `=======` is your current branch and the part below is the branch you're merging in.
- Rebase golden rule: only rebase commits that exist only on your machine, never ones you already pushed.

---
