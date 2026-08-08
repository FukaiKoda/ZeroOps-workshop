# Exercise 03 — Multi-Job Pipeline ⭐⭐

## Story
Backend and Frontend teams work independently in the project and their automated testing pipelines should run in parallel to minimize overall build duration.

## Objective
Learn the difference between `jobs:` and `steps:`, and create a workflow containing two independent jobs (`backend` and `frontend`) that run concurrently by default.

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex03_multi_job_pipeline/`

Create your workflow file inside this folder (e.g. `ex03_multi_job_pipeline/workflow.yml`).

## Tasks

Define a workflow containing a `jobs:` block with **two top-level jobs**: `backend` and `frontend`.

1. **Job 1: `backend`**
   - Runs on `ubuntu-latest`.
   - Step 1: Checkout using `actions/checkout@v4`.
   - Step 2: Echo step printing `"Testing backend"`.

2. **Job 2: `frontend`**
   - Runs on `ubuntu-latest`.
   - Step 1: Checkout using `actions/checkout@v4`.
   - Step 2: Echo step printing `"Testing frontend"`.

---

> 💡 **Key Concept: `jobs:` vs `steps:`**
> - **`steps`** inside a single job execute **sequentially** (one after another in the same runner environment).
> - **`jobs`** at the top level execute **in parallel** by default (on separate virtual runner instances).


