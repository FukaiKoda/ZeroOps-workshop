# 🔬 Lab 09: The Full Stack
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

- Submission directory: `~/rendudevops/ex09_docker_full_stack/`
- Directory Structure:

```text
ex09_docker_full_stack/
├── docker-compose.yml      # You will create this
├── frontend/
│   ├── Dockerfile          # Provided
│   └── index.html          # Provided
├── backend/
│   ├── Dockerfile          # Provided
│   ├── app.py              # Provided
│   └── requirements.txt    # Provided
└── database/
    └── init.sql            # Provided
```

**frontend/Dockerfile:**

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
```

**frontend/index.html:**

```html
<!DOCTYPE html>
<html>
<head><title>Grade Me Portal</title></head>
<body>
    <h1>🎓 Grade Me Student Portal</h1>
    <p>API Endpoint: <a href="http://localhost:5000/health">Backend Health</a></p>
</body>
</html>
```

**backend/Dockerfile:**

```dockerfile
FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

**backend/requirements.txt:**

```text
flask==3.0.0
psycopg2-binary==2.9.9
```

**backend/app.py:**

```python
from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'grademe'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'secretpass')
    )

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "backend"})

@app.route('/submissions')
def submissions():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT student_name, grade FROM submissions;')
    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{"name": r[0], "grade": r[1]} for r in results])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**database/init.sql:**

```sql
CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    student_name VARCHAR(100),
    grade INTEGER
);

INSERT INTO submissions (student_name, grade) VALUES
    ('Alice', 95),
    ('Bob', 87),
    ('Charlie', 92);
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

## 📋 Cheat Sheet

| Command | What it actually does |
|---------|----------------------|
| `docker compose up --build` | Rebuilds images before starting |
| `docker compose build` | Only builds/rebuilds images |
| `docker compose up --build -d` | Rebuild and start in background |
| `docker compose logs backend` | View logs for one specific service |
| `depends_on:` | Starts services in order (but doesn't wait for "ready") |

## 📄 Multi-Service Compose Pattern

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```