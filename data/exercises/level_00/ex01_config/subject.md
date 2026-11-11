# 🔬 Lab 02: Introduce Yourself
## "Teaching Git Who You Are"

## 🔑 Core Concepts

- Configuration levels: `--global` (all your repositories) vs `--local` (current repository)
- Committer identity (`user.name` and `user.email`) stamped onto every commit
- Productivity aliases as terminal shortcuts for frequent commands

## 🧩 Scenario
Your commits display a generic or wrong author name on team dashboards, and typing verbose `git log` options every time slows you down. The lead asks you to configure your Git identity and create two essential aliases.

## 🎯 Objective
Configure your Git identity, create two aliases, and document your configuration in `config-report.txt`.

## 📥 Provided & Work Directory

- **Work directory:** `~/rendudevops/ex01_config/`
- Work inside or next to your `pocket-recipes/` repository:
  ```bash
  cd ~/rendudevops/ex01_config/pocket-recipes
  ```
- **Submission:** This lab is evaluated from your local files in `~/rendudevops/ex01_config/`.

---

## 🛠️ Task List (Split into Parts)

### Part 1 — Set Your Git Identity
1. Inspect your current settings:
   ```bash
   git config --list
   ```
2. Configure your name and email globally (use the email matching your GitHub account):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```
3. Set `main` as the default branch name for newly initialized repositories:
   ```bash
   git config --global init.defaultBranch main
   ```

### Part 2 — Create Productivity Aliases
1. Create the short status alias `st` (which displays compact status with branch info):
   ```bash
   git config --global alias.st "status -sb"
   ```
2. Create the visual log graph alias `lg`:
   ```bash
   git config --global alias.lg "log --oneline --graph --all --decorate"
   ```
3. Test both aliases inside `pocket-recipes/`:
   ```bash
   git st
   git lg
   ```

### Part 3 — Generate Configuration Report (`config-report.txt`)
Save a report file named `config-report.txt` in your exercise folder (`~/rendudevops/ex01_config/config-report.txt` or inside `pocket-recipes/`):
```bash
{
  echo "user.name=$(git config user.name)"
  echo "user.email=$(git config user.email)"
  echo "alias.st=$(git config alias.st)"
  echo "alias.lg=$(git config alias.lg)"
} > config-report.txt
```
*(Alternatively, `git config --list > config-report.txt` is also accepted).*

### ⭐ Bonus (Optional)
Inside `pocket-recipes/`, set a repository-specific local email override:
```bash
git config --local user.email "work@example.com"
```
Make a quick commit, verify the author with `git log -1 --format="%an <%ae>"`, then remove the local override:
```bash
git config --local --unset user.email
```

---

## ⚠️ Constraints

- Do not use `--system` configuration.
- `config-report.txt` must contain your username, email, and both aliases.

---

## 🧪 Grading Checklist

The grader evaluates your submission across three distinct parts:

| Part | Description | What the grader checks |
|:---:|:---|:---|
| **Part 1** | Report File | `config-report.txt` exists in the exercise directory or repository. |
| **Part 2** | Git Identity | `config-report.txt` documents your `user.name` and `user.email`. |
| **Part 3** | Git Aliases | `config-report.txt` documents `alias.st` (status) and `alias.lg` (log). |

## 🧠 Hints

- Precedence rule: `--local` settings override `--global` settings.
- If you made a typo setting an alias, simply re-run the `git config` command with the corrected string.
