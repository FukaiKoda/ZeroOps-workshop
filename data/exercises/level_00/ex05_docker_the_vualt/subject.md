# 🔬 Lab 06: The Vault
## "Persistent Data with Named Volumes"

## 🔑 Core Concepts

- Named volumes vs bind mounts
- Data persistence across container destruction
- Volume lifecycle: `create`, `ls`, `inspect`, `rm`
- Why databases must use volumes

## 🧩 Scenario

Disaster struck. A junior developer accidentally ran `docker rm` on the Grade Me database container. All student submissions were lost.

The Lead Architect is furious: "This should never happen again."

Your mission: set up PostgreSQL with a **named volume** so that even if the container is destroyed, the data survives.

You must prove persistence by:

- Creating data inside the database
- Destroying the container completely
- Creating a new container and showing the data is still there

## 🎯 Objective

By the end of this lab, you should be able to:

- Create and manage named volumes
- Attach volumes to containers
- Prove data persists after container destruction
- Understand when to use volumes vs bind mounts

## 📥 Provided

- Docker image: `postgres:15-alpine`
- File: `init.sql` (creates a test table and inserts 3 rows)

`init.sql` content:

```sql
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100),
    grade INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO submissions (student_name, grade) VALUES
    ('Alice', 95),
    ('Bob', 87),
    ('Charlie', 92);
```

## 🛠️ Task List

### Part A: Create the Vault

- Create a named volume called `grademe-db-data`.
- Verify the volume exists using `docker volume ls`.

### Part B: First Database (The Original)

- Run a PostgreSQL container with:
  - Name: `grademe-db`
  - Volume: `grademe-db-data` mounted to `/var/lib/postgresql/data`
  - Environment variables:
    - `POSTGRES_PASSWORD=secretpass`
    - `POSTGRES_DB=grademe`
- Wait ~5 seconds for PostgreSQL to initialize.
- Copy `init.sql` into the container and execute it to create the test data.
- Verify the data exists by querying the `submissions` table.

### Part C: Destroy and Resurrect

- Stop and remove the `grademe-db` container completely.
- Verify the container is gone (`docker ps -a`).
- Create a new PostgreSQL container with:
  - Name: `grademe-db-new`
  - Same volume: `grademe-db-data`
  - Same environment variables
- Query the `submissions` table again.
- The data should still be there.

Important: Submit/Grade **after Part C** (while `grademe-db-new` exists), before doing cleanup.

### Part D: Cleanup (after you pass grading)

- Stop and remove the new container.
- Remove the volume (only when you are sure you don't need it).

## ⚠️ Constraints

- You must use a **named volume**, not a bind mount.
- The volume must be named exactly `grademe-db-data`.
- Do not use bind-mount syntax like `-v /host/path:/container/path`.

## 🧪 Validation

After Part C, run:

```bash
docker exec grademe-db-new psql -U postgres -d grademe -c "SELECT COUNT(*) FROM submissions;"
```

Expected output:

```text
 count
-------
     3
(1 row)
```

## 🧠 Hints

- PostgreSQL stores data in `/var/lib/postgresql/data`.
- Use `docker cp` to copy files into a container.
- You can run SQL files like this:

```bash
docker exec <container> psql -U postgres -d grademe -f /path/to/file.sql
```

## 📋 Cheat Sheet

### Volumes

| Command | What it does |
|---|---|
| `docker volume create X` | Creates an empty named volume (a "vault") |
| `docker volume ls` | Lists all volumes |
| `docker volume inspect X` | Shows volume details (name, driver, mountpoint) |
| `docker volume rm X` | Deletes a volume (data is lost) |

### Mounting

| Syntax | Meaning |
|---|---|
| `-v myvolume:/data` | Named volume mounted at `/data` |
| `-v /host/path:/data` | Bind mount from host folder (NOT allowed here) |

### Useful container commands

| Command | What it does |
|---|---|
| `docker cp file.sql container:/tmp/file.sql` | Copies a file into a running container |
| `docker exec <db> psql -U postgres -d grademe` | Opens psql inside the container |

## 🆚 Volume vs Bind Mount — When to Use?

| Use case | Best choice |
|---|---|
| Database persistence | ✅ Named volume |
| Local dev (hot reload) | ✅ Bind mount |
| Production deployments | ✅ Named volume |
| Sharing code during dev | ✅ Bind mount |
| Backing up application data | ✅ Named volume |