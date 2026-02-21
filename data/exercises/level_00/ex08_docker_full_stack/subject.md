# 🔬 Lab 08: The Full Stack
## "Multi-Service Application"

## 🔑 Core Concepts

- Multi-service architecture (frontend + backend + database)
- Building custom images in Compose (`build:` vs `image:`)
- Service dependencies and startup order (`depends_on`)
- Inter-service communication via DNS

## 🧩 Scenario

It's time to deploy the complete Grade Me system:

- **Frontend**: Nginx serving the student portal
- **Backend**: A Python API that handles grading logic
- **Database**: PostgreSQL storing all submissions

All three must work together seamlessly. The frontend calls the backend, the backend queries the database. One `docker compose up` should bring the entire system online.

## 🎯 Objective

By the end of this lab, you should be able to:

- Define a multi-service application in Compose
- Build custom images from Dockerfiles within Compose
- Configure services to communicate with each other
- Understand service dependencies and health

## 📥 Provided

- Submission directory: `~/rendudevops/ex08_docker_full_stack/`
- The following files will be generated automatically after your first submission:

```text
ex08_docker_full_stack/
├── docker-compose.yml      # You will create this
├── frontend/
│   ├── Dockerfile          # Auto-generated
│   └── index.html          # Auto-generated
├── backend/
│   ├── Dockerfile          # Auto-generated
│   ├── app.py              # Auto-generated
│   └── requirements.txt    # Auto-generated
└── database/
    └── init.sql            # Auto-generated
```

## 🛠️ Task List

### Part A: Define the Database Service

- Create `docker-compose.yml` with a `db` service:
	- Image: `postgres:15-alpine`
	- Environment: `POSTGRES_PASSWORD`, `POSTGRES_DB=grademe`
	- Volumes:
		- Named volume `db-data` for persistence
		- Bind mount `./database/init.sql` to `/docker-entrypoint-initdb.d/init.sql`

### Part B: Define the Backend Service

- Add a `backend` service:
	- Build from: `./backend`
	- Ports: Map `5000:5000`
	- Environment: `DB_HOST=db`, `DB_PASSWORD=secretpass`
	- Depends on: `db`

### Part C: Define the Frontend Service

- Add a `frontend` service:
	- Build from: `./frontend`
	- Ports: Map `8080:80`
	- Depends on: `backend`

### Part D: Launch and Test

- Build and start all services:

```bash
docker compose up --build -d
```

- Verify all three services are running:

```bash
docker compose ps
```

- Test the frontend:

```bash
curl localhost:8080
```

- Test the backend health:

```bash
curl localhost:5000/health
```

- Test the full stack:

```bash
curl localhost:5000/submissions
```

### Part E: Observe the Magic

- Check the logs for all services:

```bash
docker compose logs
```

- Notice how the backend connects to `db` by name (DNS magic!).
- Stop everything with `docker compose down`.

## ⚠️ Constraints

- You **must** use `build:` for frontend and backend, not pre-built images.
- The database must be initialized with the provided `init.sql`.
- Services must be able to communicate by name (DNS).
- The volume must be a **named volume**, not a bind mount.

## 🧪 Validation

Run the following to verify your work:

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

- `build: ./path` tells Compose to build from a Dockerfile in that directory.
- PostgreSQL runs init scripts from `/docker-entrypoint-initdb.d/` on first start.
- `depends_on` only waits for container start, not for app readiness.
- The backend might fail initially if DB isn't ready - it will retry.
- If database doesn't have data, try: `docker compose down -v && docker compose up -d`