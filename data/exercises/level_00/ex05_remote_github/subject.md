# 🔬 Lab 06: Hello, Remote
## "Connecting Your Repo to GitHub"

## 🔑 Core Concepts

- A remote is another copy of the repository (`origin` by convention)
- `git push -u` links your local branch to the remote one
- `git fetch` downloads, `git pull` downloads **and** merges

## 🧩 Scenario
Your Pocket Recipes history only exists on your laptop. If it breaks, everything is gone. Time to publish it and see how a change made elsewhere reaches you.

## 🎯 Objective
Publish your repo to a remote and receive a change made on the remote.

## 📥 Provided

- The `pocket-recipes` repository from Lab 01, with `main` as the current branch.
- A GitHub account with authentication already set up (token, SSH key or `gh auth login`).
- **No account?** Use a local fake remote: `git init --bare ../fake-github.git`, and use its path wherever the lab says `<url>`.

## 🛠️ Task List

- On GitHub, create an **empty** repository named `pocket-recipes` (no README, no `.gitignore`, no license).
- In your local repo, run `git remote add origin <url>`, then `git remote -v` to check.
- Publish with `git push -u origin main`, then refresh the GitHub page.
- On GitHub, add a `README.md` through the web interface and commit it there.
- Back in the terminal, run `git fetch`, then `git status`. Your branch is now "behind".
- Run `git pull` and confirm that `README.md` appeared.
- ⭐ **Bonus:** make a second copy with `git clone <url> ../pocket-recipes-clone`.

## ⚠️ Constraints

- Push only `main`.
- Never use `git push --force`.

## 🧪 Validation

- `git remote -v` shows `origin`.
- `git status` says `Your branch is up to date with 'origin/main'`.

## 🧠 Hints

- GitHub no longer accepts your account password over HTTPS. Use a personal access token or an SSH key.
- If Git can't find `main`, check your branch name with `git branch --show-current` and rename it with `git branch -M main`.
- `git fetch` never changes your files, but `git pull` can.

---
