# 🔬 Lab 09: Ship It!
## "Production-Ready Practices"

## 🔑 Core Concepts

- Environment files (`.env`) for secure configuration
- Health checks for container reliability monitoring
- Service dependencies with health conditions
- Restart policies for automatic recovery
- Resource limits (CPU/Memory) for stability

## 🧩 Scenario

The Grade Me system is ready for production! But before deploying, the DevOps team has a strict checklist:

- **No secrets in code** - Passwords must live in `.env` files, not hardcoded in YAML
- **Health checks** - Docker needs to know if a container is actually healthy, not just "running"
- **Self-healing** - If something crashes at 3 AM, it should recover automatically
- **Resource limits** - One runaway container shouldn't kill the entire server

Your mission: Harden the Lab 09 compose file for production deployment. This is the final lab - prove you're ready to ship!

## 🎯 Objective

By the end of this lab, you should be able to:

- Create and use `.env` files for configuration management
- Implement health checks for critical services
- Configure service dependencies with health conditions
- Set up automatic restart policies for resilience
- Apply resource limits to prevent runaway containers

## 📥 Provided

- Submission directory: `~/rendudevops/ex09_docker_ship_it/`
- The base files from Lab 08 will be generated automatically after your first submission.
- Directory structure:

```text
ex09_docker_ship_it/
├── docker-compose.yml     # You will create/enhance this
├── .env                   # You will create this
├── .gitignore             # You will create this
├── frontend/
│   ├── Dockerfile         # Auto-generated
│   └── index.html         # Auto-generated
├── backend/
│   ├── Dockerfile         # Auto-generated (includes curl for healthcheck)
│   ├── app.py             # Auto-generated
│   └── requirements.txt   # Auto-generated
└── database/
    └── init.sql           # Auto-generated
```

## 🛠️ Task List

### Part A: Environment Configuration

Create a `.env` file to externalize sensitive configuration:

```text
POSTGRES_PASSWORD=supersecretprod
POSTGRES_DB=grademe
DB_HOST=db
BACKEND_PORT=5000
FRONTEND_PORT=8080
```

Update `docker-compose.yml` to use `${VARIABLE}` syntax:

```yaml
# Before (hardcoded - BAD!)
environment:
  - POSTGRES_PASSWORD=secretpass

# After (from .env - GOOD!)
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

Verify configuration loads correctly:

```bash
docker compose config
```

### Part B: Health Checks

Add a health check to the `db` service:

```yaml
db:
  image: postgres:15-alpine
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

Add a health check to the `backend` service:

```yaml
backend:
  build: ./backend
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

Update the backend service to wait for db to be **healthy**, not just started:

```yaml
backend:
  depends_on:
    db:
      condition: service_healthy
```

Start the stack and observe health status:

```bash
docker compose up -d
docker compose ps
```

### Part C: Restart Policies

Add `restart: unless-stopped` to **all** services:

```yaml
frontend:
  restart: unless-stopped
  # ... rest of config

backend:
  restart: unless-stopped
  # ... rest of config

db:
  restart: unless-stopped
  # ... rest of config
```

Test the restart policy:

```bash
# Get container name
docker compose ps

# Kill it
docker kill <container-name>

# Wait 5 seconds, then check - it should be back!
docker compose ps
```

### Part D: Resource Limits

Add resource limits to the `backend` service:

```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 256M
      reservations:
        memory: 128M
```

Optionally add limits to other services for extra hardening.

### Part E: Security Best Practice

Create a `.gitignore` file to protect secrets:

```text
.env
*.log
```

Never commit `.env` files to version control!

### Part F: Final Verification

Restart the entire stack with production configuration:

```bash
docker compose down
docker compose up -d
```

Verify all health checks pass:

```bash
docker compose ps
```

Test the full stack:

```bash
curl localhost:8080                  # Frontend
curl localhost:5000/health           # Backend health
curl localhost:5000/submissions      # Database connectivity
```

## ⚠️ Constraints

- **No hardcoded passwords** in `docker-compose.yml` - use `${VAR}` syntax
- Required environment variables: `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_HOST`
- Health checks required for: `db`, `backend`
- Restart policy required for: `frontend`, `backend`, `db`
- Memory limits required for: `backend` (CPU limits are optional - some systems don't support them)
- The `.env` file should be in `.gitignore`

## 🧪 Validation

Run the following to verify your work:

```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

Expected Output:

```text
NAME                              STATUS           HEALTH
ex09_docker_ship_it-backend-1     Up 30 seconds    healthy
ex09_docker_ship_it-db-1          Up 35 seconds    healthy
ex09_docker_ship_it-frontend-1    Up 28 seconds    healthy
```

Test the full stack:

```bash
curl -s localhost:5000/submissions | python3 -m json.tool
```

Expected Output:

```json
[
    {"name": "Alice", "grade": 95},
    {"name": "Bob", "grade": 87},
    {"name": "Charlie", "grade": 92}
]
```

## 🧠 Hints

- Health checks run **INSIDE** the container, so paths must be valid inside the container.
- `service_healthy` condition requires the dependency to have a health check defined first.
- For local testing with resource limits, ensure Docker has enough resources allocated.
- **CPU limits are optional** - some Linux kernels don't support NanoCPUs. Memory limits are required.
- If a container keeps crashing, check logs: `docker compose logs <service>`.
- The backend healthcheck uses `curl`, so make sure the backend Dockerfile has curl installed.
- Create `.gitignore` before your first commit to prevent leaking secrets!


## 🔄 Restart Policies

| Policy | Behavior |
|--------|----------|
| `no` | Never restart (default) |
| `always` | Always restart, even if manually stopped |
| `on-failure` | Restart only if exit code is non-zero |
| `unless-stopped` | Restart unless manually stopped ✅ **Recommended** |

## 🏁 Workshop Complete!

Congratulations! You've completed the Docker Workshop. You've learned:

- ✓ Running containers and managing the lifecycle
- ✓ Building custom images with Dockerfiles
- ✓ Managing volumes, networks, and secrets
- ✓ Orchestrating multi-container applications
- ✓ Production hardening with health checks and policies

**Next Steps:**
- Explore Docker Swarm for cluster orchestration
- Learn Kubernetes for enterprise deployments
- Set up CI/CD pipelines with Docker
- Master multi-stage builds for optimization