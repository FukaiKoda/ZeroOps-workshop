# 🔬 Lab 02: Coming Soon
## "The Full Container Lifecycle"

## 🔑 Core Concepts

- Running containers in detached mode (`-d`)
- Port mapping (`-p host:container`)
- Naming containers for organization (`--name`)
- Container lifecycle commands (`stop`, `start`, `rm`)
- Diagnostic tools (`logs`, `exec`, `stats`)

## 🧩 Scenario

The marketing team is impatient. They need the **"Coming Soon"** landing page deployed now, but they also want you to prove you have full operational control over the deployment.

You must demonstrate that you can:

- Deploy the web server properly
- Monitor and troubleshoot it if something goes wrong
- Access the container internals for debugging
- Clean up after yourself like a professional

The Lead Architect is watching. No "ghost containers" allowed on this server.

## 🎯 Objective

By the end of this lab, you should be able to:

- Run a container in detached mode with proper naming and port mapping
- Use Docker diagnostics to inspect a running container
- Execute commands inside a running container
- Manage the full container lifecycle (start → stop → start → remove)

## 📥 Provided

- Submission directory: `~/rendudevops/ex02_docker_coming_soon/`

## 🛠️  Task List

### Part A: Deployment

- Pull the `nginx:alpine` image from Docker Hub.
- Run the image in detached mode with:
	- Name: `coming-soon`
	- Host port `8080` mapped to container port `80`
- Verify the page is accessible:

```bash
curl localhost:8080
```

### Part B: Monitoring & Inspection

Tasks to complete:
- View the last 10 lines of the container's logs.
- Check the container's real-time resource usage (CPU/Memory).
- Execute a shell (`/bin/sh`) inside the running container.
- From inside the container, verify Nginx is running by checking its version.
- Exit the container shell.

Save the output of diagnostic commands to `proof.txt` in your submission directory:

```bash
cd ~/rendudevops/ex02_docker_coming_soon
docker logs --tail 10 coming-soon >> proof.txt 2>&1
docker stats --no-stream coming-soon >> proof.txt 2>&1
docker exec coming-soon nginx -v >> proof.txt 2>&1
```

### Part C: Lifecycle Management

- Stop the container.
- Verify it still exists but is not running (hint: `docker ps` vs `docker ps -a`).
- Start the container again and confirm the page is accessible.
- Stop and remove the container in a single operation.
- Verify no containers remain (running or stopped).

## ⚠️ Constraints

- You must use `nginx:alpine` (not `nginx:latest`).
- The container must be named exactly `coming-soon`.
- No ghost containers should remain after completion.

## 🧪 Validation

After Part C, run:

```bash
curl -s localhost:8080 > /dev/null && echo "FAIL: Container still running" || echo "PASS: Container removed"
docker ps -a | grep coming-soon && echo "FAIL: Ghost container exists" || echo "PASS: Clean workspace"
```

Expected output:

```text
PASS: Container removed
PASS: Clean workspace
```

## 🧠 Hints

- Use `docker run -d` to run in detached (background) mode.
- The `-p` flag maps ports as `host:container`, so `-p 8080:80` makes port 80 inside the container accessible on port 8080 on your machine.
- `docker ps` only shows running containers; use `docker ps -a` to see all containers including stopped ones.
- You can combine stop and remove with `docker rm -f <container>` (force removes even if running).
- If `docker logs` shows no output, make sure the container is running first!

## 📋 Cheat Sheet

| Command | What it actually does |
|---------|----------------------|
| `docker run -d --name X -p H:C image` | Run container in background with name X, port mapping H→C |
| `docker logs <name>` | View container output/logs |
| `docker logs --tail N <name>` | View last N lines of logs |
| `docker stats <name>` | Real-time resource usage (Ctrl+C to exit) |
| `docker stats --no-stream <name>` | One-shot resource snapshot |
| `docker exec <name> <cmd>` | Run a command inside the container |
| `docker exec -it <name> /bin/sh` | Open interactive shell inside container |
| `docker stop <name>` | Gracefully stop a running container |
| `docker start <name>` | Start a stopped container |
| `docker rm <name>` | Remove a stopped container |
| `docker rm -f <name>` | Force remove (even if running) |
| `docker ps` | List running containers |
| `docker ps -a` | List all containers (including stopped) |

## 🧠 Hints

- Alpine-based images use `/bin/sh` (not `/bin/bash`).
- `docker stats` runs until you exit (Ctrl+C).
- `docker rm -f` force stops and removes a running container.

## 📋 Cheat Sheet

| Command | What it does |
|---|---|
| `docker run -d ...` | Runs a container in "background mode" (detached) |
| `docker run --name X ...` | Gives your container a memorable name |
| `docker run -p 8080:80 ...` | Maps host port 8080 → container port 80 |
| `docker ps` | Shows only running containers |
| `docker ps -a` | Shows all containers (including stopped "ghosts") |
| `docker logs <name>` | Reads container stdout/stderr |
| `docker logs -n 10 <name>` | Shows only the last 10 log lines |
| `docker stats` | Live CPU/Memory monitor (like `top` for containers) |
| `docker exec -it <name> sh` | Opens a shell inside a running container |
| `docker stop <name>` | Gracefully stops a container |
| `docker rm <name>` | Removes a stopped container |
| `docker rm -f <name>` | Force-stops and removes a container |
