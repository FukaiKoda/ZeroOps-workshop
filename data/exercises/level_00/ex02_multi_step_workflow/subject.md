# Exercise 02 — GitHub Context Variables ⭐⭐

## Story
Your team wants pipelines to know what they're building — including repository name, branch, and commit SHA.

## Objective
Create a single-job GitHub Actions workflow that accesses and prints GitHub context variables using the `${{ github.X }}` expression syntax.

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex02_multi_step_workflow/`

Create your workflow file inside this folder (e.g., `ex02_multi_step_workflow/workflow.yml`).

## Tasks (Single Job)

Your workflow must contain a single job that performs:

1. **Checkout**: Uses `actions/checkout@v4`.
2. **Echo Repository**: `echo "Repository: ${{ github.repository }}"`
3. **Echo Branch**: `echo "Branch: ${{ github.ref_name }}"`
4. **Echo Commit SHA**: `echo "Commit SHA: ${{ github.sha }}"`

---

> 💡 **Important Concept: Context Syntax vs. Shell Variables**
> - `${{ github.repository }}` is evaluated by **GitHub Actions** *before* the script is sent to the runner shell.
> - Shell environment variables (e.g. `$GITHUB_REPOSITORY` or `env:` variables) are evaluated at runtime by **Bash**.
> 
> Make sure you use the explicit `${{ github.X }}` context expression syntax in this exercise!


