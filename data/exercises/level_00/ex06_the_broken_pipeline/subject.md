# Exercise 06 — The Broken Pipeline ⭐⭐⭐

## Story
A teammate pushed three broken workflow files to the repository and CI won't even start. Instead of memorizing a single syntax fix, you need to diagnose and fix three separate real-world broken YAML files to build real debugging instincts.

## Objective
Identify and resolve common YAML syntax, indentation, and key naming errors across three workflow files.

## Target Directory
In your portfolio repository (`zeroops-devops`), create the exercise directory:
`ex06_the_broken_pipeline/`

Create three fixed workflow files inside this directory:
1. `06a_colons.yml`
2. `06b_indentation.yml`
3. `06c_key_name.yml`

---

## Broken Files Overview

### File 1: `06a_colons.yml` (Missing Colons)
```yaml
name: Fix Colons
on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name Checkout
        uses actions/checkout@v4
      - run echo Hello
```
**Bug:** Missing colons after `name`, `uses`, and `run`.

### File 2: `06b_indentation.yml` (Bad Indentation)
```yaml
name: Fix Indentation
on: push

jobs:
  build:
runs-on: ubuntu-latest
    steps:
      - run: echo hi
```
**Bug:** `runs-on` is unindented and invalid YAML syntax under `jobs.build`.

### File 3: `06c_key_name.yml` (Wrong Key Name)
```yaml
name: Fix Key Name
on: push

jobs:
  build:
    runs-on: ubuntu-latest
    step:
      - run: echo hi
```
**Bug:** Uses invalid key `step:` instead of `steps:`.

---

## Tasks
Fix all three files so that each parses as valid YAML and contains valid jobs with `runs-on` and `steps`.
