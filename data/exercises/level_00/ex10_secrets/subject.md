# Exercise 10 — Secrets ⭐⭐⭐

## Story
API keys, access tokens, and passwords must never be committed to source code or hardcoded in workflow files. Pass encrypted secrets securely into jobs using GitHub Repository Secrets.

## Objective
Learn end-to-end secret configuration in GitHub Actions and practice safe secret debugging techniques.

## Setup Step in GitHub Repository
Before writing your workflow:
1. Go to your repository on GitHub.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret**.
4. Name: `API_KEY`
5. Value: any dummy string (e.g. `secret_api_token_12345`).

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex10_secrets/`

Create your workflow file inside this folder (e.g. `ex10_secrets/workflow.yml`).

## Tasks

Define a workflow containing:

1. **Checkout**: Uses `actions/checkout@v4`.
2. **Environment Secret Injection**: Map the secret into a step's `env:` block:
   ```yaml
   env:
     API_KEY: ${{ secrets.API_KEY }}
   ```
3. **Safe Secret Debugging**: Print the secret's **character length** instead of the secret itself:
   ```bash
   run: echo "Key length: ${#API_KEY}"
   ```

---

> ⚠️ **Security Habit: Safe Secret Debugging**
> GitHub Actions automatically masks secrets printed to build logs. However, good security hygiene dictates **never** echoing secret values directly. Printing character length (`${#API_KEY}`) verifies the secret exists and is non-empty without leaking data.

---

## Example Workflow Structure

```yaml
name: Secrets Management
on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Safe Secret Debugging
        env:
          API_KEY: ${{ secrets.API_KEY }}
        run: echo 'Key length:' ${#API_KEY}
```
