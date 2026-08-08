# Exercise 07 — Marketplace Actions ⭐⭐

## Story
Instead of writing complex tool installation scripts by hand, modern CI pipelines leverage community Marketplace Actions. Pinning action versions ensures your builds remain deterministic and reproducible over time.

## Objective
Learn how to use reusable Marketplace Actions (`actions/setup-python@v5`) and pass configuration options using the `with:` block.

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex07_marketplace_actions/`

Create your workflow file inside this folder (e.g. `ex07_marketplace_actions/workflow.yml`).

## Tasks

Define a workflow that performs:

1. **Checkout**: Uses `actions/checkout@v4`.
2. **Setup Python**: Uses `actions/setup-python@v5` pinned version.
3. **Configure Version**: Pass `python-version: '3.11'` inside a `with:` block.
4. **Verify Installation**: Execute a step running `python --version`.

---

> 💡 **Key Concept: Action Pinning & `with:` Inputs**
> - **Action Pinning** (e.g. `@v5` or commit SHA) prevents breaking changes when third-party actions update.
> - **`with:`** block passes input parameters required by the action.


