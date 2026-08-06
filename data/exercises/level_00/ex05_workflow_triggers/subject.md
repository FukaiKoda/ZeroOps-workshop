# Exercise 05 — Workflow Triggers ⭐

## Story
The engineering team wants to conserve build time and run CI workflows only when necessary: on Pull Requests, and on direct pushes to the primary `main` production branch.

## Objective
Learn how to configure the `on:` trigger block with event types and branch filters.

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex05_workflow_triggers/`

Create your workflow file inside this folder (e.g. `ex05_workflow_triggers/workflow.yml`).

## Tasks

Configure your workflow `on:` trigger section to include:

1. **Pull Requests**: Trigger on any `pull_request` event.
2. **Filtered Push**: Trigger on `push` events targeting branch `main` (`branches: [main]` or `branches: ['main']`).

---

> 💡 **Key Concept: Event Triggers & Branch Filters**
> Workflows can trigger on specific events like `push`, `pull_request`, or `schedule`. Branch filters (`branches:`) restrict execution so pipelines only run when relevant branches change.

---

## Example Workflow Structure

```yaml
name: Workflow Triggers
on:
  pull_request:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Validate Triggers
        run: echo "Triggered on PR or push to main!"
```
