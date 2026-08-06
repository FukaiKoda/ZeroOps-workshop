# Exercise 09 — Environment Variables ⭐⭐

## Story
Configure reusable workflow-wide or job-level configuration values without hardcoding them into every step.

## Objective
Learn how to define environment variables in an `env:` block and access them inside runner shell commands using shell variable interpolation (`$VAR`).

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex09_environment_variables/`

Create your workflow file inside this folder (e.g. `ex09_environment_variables/workflow.yml`).

## Tasks

Define a workflow containing:

1. **`env:` Block**: Define workflow-level or job-level environment variables:
   - `PROJECT_NAME: "ZeroOps"` (or your custom project name)
   - `AUTHOR: "DevOpsTeam"` (or your name)
2. **Checkout**: Uses `actions/checkout@v4`.
3. **Print Shell Variables**: Execute a step that prints both variables using shell syntax:
   `run: echo "$PROJECT_NAME by $AUTHOR"`

---

> 💡 **Key Concept: `env:` Shell Variables vs. `${{ github.X }}` Context Expressions**
> - **`${{ github.X }}` (Exercise 02)** is evaluated by GitHub Actions before sending the script to the runner.
> - **`$PROJECT_NAME` (Exercise 09)** is an environment variable passed into the shell and evaluated at runtime by Bash.

---

## Example Workflow Structure

```yaml
name: Environment Variables
on: push

env:
  PROJECT_NAME: "ZeroOps"
  AUTHOR: "DevOpsTeam"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Print Env Variables
        run: echo "$PROJECT_NAME by $AUTHOR"
```
