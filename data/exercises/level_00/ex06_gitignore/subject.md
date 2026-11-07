# 🔬 Lab 07: The Bouncer
## "Keeping Junk and Secrets Out of Git"

## 🔑 Core Concepts

- `.gitignore` patterns
- Ignoring only works on **untracked** files
- Un-tracking a file committed by mistake with `git rm --cached`

## 🧩 Scenario
A teammate committed a `.env` file containing an API key on day one, and now log files and build output keep showing up in `git status`. Set up the bouncer and clean up the mess.

## 🎯 Objective
Ignore logs, build output and secrets, and stop tracking a file that was committed by mistake.

## 📥 Provided

- A practice repo. Create it with this script:

```bash
git init -b main lab07 && cd lab07
echo "print('hello')" > app.py
echo "API_KEY=super-secret-123" > .env
git add . && git commit -m "Initial commit"
echo "debug line" > debug.log
mkdir build && echo "compiled" > build/output.bin
```

## 🛠️ Task List

- Run `git status`. `debug.log` and `build/` show up as untracked.
- Create a `.gitignore` file with three lines: `*.log`, `build/` and `.env`.
- Run `git status` again. Which files disappeared? Check one with `git check-ignore -v debug.log`.
- Edit `.env` (change the value) and run `git status`. It still shows as modified. Why? (It's already tracked.)
- Stop tracking it but keep it on disk: `git rm --cached .env`, then commit with `Stop tracking .env`.
- Edit `.env` again. `git status` should stay quiet now. Commit `.gitignore` too.

## ⚠️ Constraints

- Do not delete `.env` from your disk. Git should only forget it.

## 🧪 Validation

- `git ls-files` lists only `.gitignore` and `app.py`.
- `ls -a` still shows `.env`.

## 🧠 Hints

- A trailing slash (`build/`) means "this is a folder".
- Un-tracking doesn't erase the secret from old commits. In real life, a leaked key must be **revoked and replaced**.
- Ready-made `.gitignore` templates live at github.com/github/gitignore.
