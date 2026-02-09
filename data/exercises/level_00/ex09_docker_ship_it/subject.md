# 🔬 Lab 10: Ship It!
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

- Submission directory: `~/rendudevops/ex10_docker_ship_it/`
- Starting point: Complete solution from Lab 09
- Directory structure:

```text
ex10_docker_ship_it/
├── docker-compose.yml     # Enhanced from Lab 09
├── .env                   # You will create this
├── .gitignore             # You will create this
├── frontend/
│   ├── Dockerfile
│   └── index.html
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── database/
    └── init.sql
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
        cpus: '0.5'
        memory: 256M
      reservations:
        cpus: '0.25'
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
- Resource limits required for: `backend`
- The `.env` file should be in `.gitignore`

## 🧪 Validation

Run the following to verify your work:

```bash
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

Expected Output:

```text
NAME                              STATUS           HEALTH
ex10_docker_ship_it-backend-1     Up 30 seconds    healthy
ex10_docker_ship_it-db-1          Up 35 seconds    healthy
ex10_docker_ship_it-frontend-1    Up 28 seconds    healthy
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
- If a container keeps crashing, check logs: `docker compose logs <service>`.
- The backend healthcheck uses `curl`, so make sure the backend Dockerfile has curl installed.
- Create `.gitignore` before your first commit to prevent leaking secrets!

## 📋 Cheat Sheet

| Command | What it actually does |
|---------|----------------------|
| `docker compose config` | Shows resolved compose file with all ${VAR} replaced |
| `docker compose ps` | Shows status and health of all services |
| `docker compose up -d` | Start all services in background |
| `docker compose down` | Stop and remove all containers |
| `docker compose logs -f` | Follow logs from all services |
| `docker kill <name>` | Force stop a container (to test restart policy) |

## 📄 Complete Production Compose Example

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "${FRONTEND_PORT:-8080}:80"
    restart: unless-stopped
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "${BACKEND_PORT:-5000}:5000"
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PASSWORD=${POSTGRES_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    depends_on:
      db:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - db-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  db-data:
```

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