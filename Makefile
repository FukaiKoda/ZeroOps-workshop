.PHONY: all install run-server run-client dev stop-server test-health test-exercise test-me test-submit docker-build docker-up docker-down docker-logs

all: dev

install:
	@echo "Installing server dependencies..."
	cd server && pip install -e .
	@echo "Installing client dependencies..."
	cd client && pip install textual typer httpx pydantic-settings click pillow

run-server:
	cd server && /usr/bin/python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

run-client:
	cd client/src && /usr/bin/python3 main.py tui

dev:
	@echo "Starting Server in background..."
	@# Start server in background and save PID
	@cd server && /usr/bin/python3 -m uvicorn src.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 & echo $$! > .server.pid
	@echo "Server started with PID `cat server/.server.pid`"
	@sleep 2
	@echo "Starting Client..."
	@-cd client/src && /usr/bin/python3 main.py tui
	@$(MAKE) stop-server

stop-server:
	@if [ -f server/.server.pid ]; then \
		PID=$$(cat server/.server.pid); \
		echo "Stopping Server (PID $$PID)..."; \
		kill $$PID && rm server/.server.pid; \
	else \
		echo "Server PID not found."; \
	fi

test-health:
	@echo "Testing Health Endpoint..."
	@curl -s http://127.0.0.1:8000/health | python3 -m json.tool

test-me:
	@echo "Testing /v1/me (uses ZEROOPS_SESSION_TOKEN env)..."
	@curl -s http://127.0.0.1:8000/v1/me -H "Authorization: Bearer $$ZEROOPS_SESSION_TOKEN" | python3 -m json.tool

test-exercise:
	@echo "Fetching next exercise for user..."
	@curl -s http://127.0.0.1:8000/v1/exercise -H "Authorization: Bearer $$ZEROOPS_SESSION_TOKEN" | python3 -m json.tool

test-submit:
	@echo "Submitting ex00-hello (requires Docker for grading to complete)..."
	@curl -s -X POST http://127.0.0.1:8000/v1/submit \
		-H "Content-Type: application/json" \
		-d '{"session_token": "'$$ZEROOPS_SESSION_TOKEN'", "exercise_slug": "ex00-hello", "files": [{"filename": "main.py", "content": "print(1)"}], "client_version": "0.1.0"}' | python3 -m json.tool

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d server
	@sleep 2
	@echo "Server is ready. Starting client..."
	docker-compose run --rm client

docker-down:
	@echo "Stopping all services...""
	docker-compose down

docker-logs:
	@echo "Showing logs..."
	docker-compose logs -f

docker-server:
	@echo "Starting only the server..."
	docker-compose up -d server
	@echo "Server running at http://localhost:8000"

docker-client:
	@echo "Starting client (requires server to be running)..."
	docker-compose run --rm client

