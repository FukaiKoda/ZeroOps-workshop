.PHONY: all install run-server run-client dev stop-server test-health test-exercise test-me test-submit

all: dev

install:
	cd server && poetry install
	cd client && poetry install

run-server:
	cd server && poetry run uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

run-client:
	cd client && poetry run python src/main.py tui

dev:
	@echo "Starting Server in background..."
	@# Start server in background and save PID
	@cd server && poetry run uvicorn src.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 & echo $$! > .server.pid
	@echo "Server started with PID `cat .server.pid`"
	@sleep 2
	@echo "Starting Client..."
	@-cd client && poetry run python src/main.py tui
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

