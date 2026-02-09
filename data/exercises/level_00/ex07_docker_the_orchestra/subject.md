# 🔬 Lab 08: The Orchestra
## "Introduction to Docker Compose"

## 🔑 Core Concepts

- The `docker-compose.yml` file structure
- Translating `docker run` commands to Compose syntax
- `services`, `ports`, `volumes`, `networks`, `environment` keys
- `docker compose up`, `down`, `ps`, `logs`

## 🧩 Scenario

The Grade Me team is tired of typing long `docker run` commands. Every time a new developer joins, they spend an hour just trying to start the local environment.

The Lead Architect demands: "One command to start everything. One command to stop everything. Document the entire infrastructure in a single file."

Your mission: Create a `docker-compose.yml` that defines a web server and database, replacing all those manual commands.

## 🎯 Objective

By the end of this lab, you should be able to:

- Write a `docker-compose.yml` file from scratch
- Define services with ports, volumes, and environment variables
- Start and stop the entire stack with one command
- View aggregated logs from all services

## 📥 Provided

- Files: `index.html` (auto-created landing page)
- Docker images: `nginx:alpine`, `postgres:15-alpine`
- Submission directory: `~/rendudevops/ex08_docker_the_orchestra/`

**index.html** (auto-created for you):

```html
<!DOCTYPE html>
<html>
<head><title>Grade Me System</title></head>
<body>
    <h1>🎓 Grade Me System</h1>
    <p>Status: <strong>Online</strong></p>
    <p>Database: <span id="db">Checking...</span></p>
</body>
</html>
```

## 🛠️ Task List

### Part A: Your First Compose File

- Create a file named `docker-compose.yml` in your submission directory.
- Define a service called `web`:
	- Image: `nginx:alpine`
	- Ports: Map host `8080` to container `80`
	- Volumes: Bind mount `./index.html` to `/usr/share/nginx/html/index.html`
- Start the stack with `docker compose up -d`.
- Verify the page is accessible:

```bash
curl localhost:8080
```

- View the logs with `docker compose logs`.
- Stop and remove everything with `docker compose down`.

### Part B: Adding the Database

- Edit `docker-compose.yml` to add a service called `db`:
	- Image: `postgres:15-alpine`
	- Environment variables:
		- `POSTGRES_PASSWORD=secretpass`
		- `POSTGRES_DB=grademe`
	- Volumes: Named volume `db-data` mounted to `/var/lib/postgresql/data`
- Declare the named volume at the top level of your compose file.
- Start the stack again.
- Verify both services are running:

```bash
docker compose ps
```

- Check the database logs specifically:

```bash
docker compose logs db
```

### Part C: Custom Network (Automatic!)

- Inspect the network created by Compose:

```bash
docker network ls
```

- Notice that Compose automatically created a network.
- Exec into the web container and ping `db` by name:

```bash
docker compose exec web ping -c 2 db
```

- It works automatically! Compose handles service discovery.

### Part D: Full Lifecycle

- Stop the stack (but keep volumes): `docker compose down`
- Start it again and verify database data persists.
- Stop and remove everything including volumes: `docker compose down -v`

## ⚠️ Constraints

- The compose file must be named exactly `docker-compose.yml`.
- You must use `nginx:alpine` for the web service.
- The database volume must be a **named volume**, not a bind mount.
- Submit/Grade with the stack **running** for bonus validation.

## 🧪 Validation

Run the following to verify your work:

```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

Expected Output:

```text
NAME                              STATUS
ex08_docker_the_orchestra-web-1   Up
ex08_docker_the_orchestra-db-1    Up
```

## 🧠 Hints

- Compose automatically creates a network for all services in the file.
- Use `docker compose` (with space), not `docker-compose` (old syntax).
- Volume syntax in compose: `volumename:/container/path`
- Bind mount syntax in compose: `./host/path:/container/path`
- Don't forget to declare named volumes at the top level!

## 📋 Cheat Sheet

| Command | What it actually does |
|---------|----------------------|
| `docker compose up` | Starts all services (foreground) |
| `docker compose up -d` | Starts all services (background/detached) |
| `docker compose down` | Stops and removes containers, networks |
| `docker compose down -v` | Also removes volumes (data lost!) |
| `docker compose ps` | Shows status of all services |
| `docker compose logs` | Shows logs from ALL services |
| `docker compose logs web` | Shows logs from only the web service |
docker compose logs -f	Follows logs in real-time
docker compose exec web sh	Opens shell in the web service
docker compose build	Rebuilds images (when using Dockerfile)
📄 Compose File Quick Reference
yaml
version: '3.8'

services:
  servicename:
    image: imagename:tag
    ports:
      - "host:container"
    environment:
      - VAR=value
    volumes:
      - ./local:/container    # bind mount
      - volumename:/container # named volume

volumes:
  volumename: