# 🔬 Lab 06: Hello, Remote
## "Connecting Your Repo to GitHub"

## 🔑 Core Concepts

- A remote is an independent copy of your repository hosted on a server (named `origin` by convention)
- Linking tracking branches with `git push -u origin main`
- Difference between `git fetch` (downloads remote commits without touching working files) and `git pull` (downloads and merges into current branch)

## 🧩 Scenario
Your Pocket Recipes repository only exists on your local machine. If your disk fails, your work is lost. You will connect your local repository to your remote workshop GitHub repository, push your commits, simulate a remote change, and synchronize your local branch.

## 🎯 Objective
Connect your local repository to GitHub, push `main`, add a `README.md` remotely, and pull the new file into your local environment.

## 📥 Provided & Work Directory

- The `pocket-recipes` repository from previous labs.
- **Work directory:** `~/rendudevops/ex05_remote_github/`
- Ensure your branch is named `main` and your repository has initial recipe commits:
  ```bash
  cd ~/rendudevops/ex05_remote_github
  # Verify or rename branch if needed:
  git branch -M main
  ```
- **Submission:** This lab requires your linked GitHub repository. Ensure your latest changes are pushed to GitHub before submitting.

---

## 🛠️ Task List (Split into Parts)

### Part 1 — Link Your GitHub Remote (`origin`)
1. Obtain your repository URL from your GitHub profile or the workshop TUI dashboard.
2. Add the remote as `origin`:
   ```bash
   git remote add origin <YOUR_GITHUB_REPO_URL>
   ```
3. Verify your configured remotes:
   ```bash
   git remote -v
   # Should list 'origin' for both fetch and push
   ```

### Part 2 — Publish Your Local History
1. Push your `main` branch and establish upstream tracking:
   ```bash
   git push -u origin main
   ```
2. Open your GitHub repository in your browser (or refresh the page) to confirm that `pasta.txt` and `salad.txt` appear on GitHub.

### Part 3 — Add Remote `README.md` and Pull Locally
1. On GitHub (via web interface, GitHub CLI, or a separate clone), create a `README.md` file with a title:
   ```markdown
   # Pocket Recipes
   ```
2. Commit the new `README.md` directly on the remote `main` branch.
3. In your local terminal, inspect the remote state without modifying local files:
   ```bash
   git fetch
   git status
   # Notice Git reports: "Your branch is behind 'origin/main' by 1 commit"
   ```
4. Integrate the remote changes into your local branch:
   ```bash
   git pull
   ```
5. Confirm that `README.md` is now present locally:
   ```bash
   ls README.md
   cat README.md
   ```

### ⭐ Bonus (Optional: Clone)
Create a second independent clone in a sibling folder to see how teammates clone your work:
```bash
git clone <YOUR_GITHUB_REPO_URL> ../pocket-recipes-clone
```

---

## ⚠️ Constraints

- Push to `origin/main`.
- Never use `git push --force`.
- Keep `README.md` at the root of the repository; it must not be empty.

---

## 🧪 Grading Checklist

The grader evaluates your submission across three distinct parts:

| Part | Description | What the grader checks |
|:---:|:---|:---|
| **Part 1** | Remote Setup | `origin` remote is properly configured. |
| **Part 2** | Push & Tracking | `main` is published and tracked on the remote GitHub repository. |
| **Part 3** | Remote Synchronization | `README.md` is created, committed, pushed to GitHub, and pulled locally. |

## 🧠 Hints

- GitHub uses Personal Access Tokens (PAT) or SSH keys for authentication rather than account passwords.
- `git fetch` updates remote-tracking branches (`origin/main`) safely without modifying your local working tree.
- `git pull` is effectively shorthand for `git fetch` followed by `git merge FETCH_HEAD`.
