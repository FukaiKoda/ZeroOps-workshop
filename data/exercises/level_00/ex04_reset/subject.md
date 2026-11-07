# 🔬 Lab 05: Time Travel
## "Undoing Commits (and Getting Them Back)"

## 🔑 Core Concepts

- What `--soft`, `--mixed` and `--hard` do
- `git reflog` as the safety net for "lost" commits

## 🧩 Scenario
A teammate made three commits and asks you to "undo the last one" in three different ways. The last way deletes real work, so you'll have to bring it back.

## 🎯 Objective
Use each reset mode on purpose, see the difference, and recover work after a `--hard` reset.

## 📥 Provided

- A practice repo. Create it with this script:

```bash
git init -b main lab05 && cd lab05
for i in 1 2 3; do echo "step $i" >> progress.txt; git add . ; git commit -m "Step $i"; done
```

## 🛠️ Task List

- Run `git lg` and `cat progress.txt` (3 commits, 3 lines).
- **Soft:** run `git reset --soft HEAD~1`, then `git status`. Your change is still staged. Recommit it: `git commit -m "Step 3 again"`.
- **Mixed:** run `git reset --mixed HEAD~1`, then `git status`. Your change is still there, but not staged. Recommit it: `git commit -am "Step 3 again"`.
- **Hard:** run `git reset --hard HEAD~1`, then `cat progress.txt`. The last line is gone.
- **Rescue:** run `git reflog`, then `git reset --hard HEAD@{1}`. Check `cat progress.txt` again.
- ⭐ **Bonus:** run `git revert HEAD --no-edit` and see how it differs from a reset (it adds a new commit instead of removing one).

## ⚠️ Constraints

- Only do this in the `lab05` repo.

## 🧪 Validation

- After the rescue, `git log --oneline` shows 3 commits and `progress.txt` has 3 lines.

## 🧠 Hints

- Memory trick: **soft** keeps changes staged, **mixed** keeps them unstaged, **hard** throws them away.
- `HEAD~1` means "one commit before the current one", and `HEAD@{1}` means "where HEAD was one move ago".
- `reflog` can't save **uncommitted** work destroyed by `--hard`. Commit first.

---
