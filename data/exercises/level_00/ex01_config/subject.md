# 🔬 Lab 02: Introduce Yourself
## "Teaching Git Who You Are"

## 🔑 Core Concepts

- The config levels: `--global` (all your repos) vs `--local` (one repo)
- Identity (`user.name` and `user.email`) attached to every commit
- Aliases as personal shortcuts

## 🧩 Scenario
Your commits show a strange author name on the team dashboard, and typing long `git log` commands every time is tiring. The lead asks you to configure Git once and for all.

## 🎯 Objective
Set your identity and two handy aliases, then use them.

## 📥 Provided

- The `pocket-recipes` repository from Lab 01.

## 🛠️ Task List

- Run `git config --list` and have a look at what is already set.
- Set your identity:
  - `git config --global user.name "Your Name"`
  - `git config --global user.email "you@example.com"`
- Set the default branch name for new repos: `git config --global init.defaultBranch main`.
- Create two aliases:
  - `git config --global alias.st "status -sb"`
  - `git config --global alias.lg "log --oneline --graph --all --decorate"`
- Try `git st` and `git lg` inside `pocket-recipes`.
- ⭐ **Bonus:** inside `pocket-recipes`, set a **local** email with `git config --local user.email "work@example.com"`. Make a tiny commit, check the author with `git log -1 --format="%an <%ae>"`, then remove the override with `git config --local --unset user.email`.

## ⚠️ Constraints

- Do not use `--system`.

## 🧪 Validation

- `git config --get user.name` prints your name.
- `git st` and `git lg` both work.

## 🧠 Hints

- Priority order: local beats global.
- Use the same email as your GitHub account, so your commits are linked to your profile later (Lab 06).

---
