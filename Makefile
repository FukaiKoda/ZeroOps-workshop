# Makefile for ZeroOps-workshop

.PHONY: all install run-server run-client dev

all: dev

install:
	cd server && poetry install
	cd client && poetry install

run-server:
	cd server && poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-client:
	cd client && poetry run python src/main.py tui

dev:
	@echo "Starting Server in background..."
	@# Start server in background and save PID
	@cd server && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 & echo $$! > .server.pid
	@echo "Server started with PID `cat .server.pid`"
	@sleep 2
	@echo "Starting Client..."
	@-cd client && poetry run python src/main.py tui
	@echo "Stopping Server..."
	@kill `cat .server.pid` && rm .server.pid

test-health:
	@echo "Testing Health Endpoint..."
	@curl -s http://127.0.0.1:8000/health | python3 -m json.tool

test-status:
	@echo "Testing Status Endpoint for 'test_user'..."
	@curl -s http://127.0.0.1:8000/v1/status/test_user | python3 -m json.tool

test-grade:
	@echo "Submitting ex00_hello for 'test_user'..."
	@curl -X POST http://127.0.0.1:8000/v1/grade \
		-H "Content-Type: application/json" \
		-d '{"user_id": "test_user", "exercise_id": "ex00_hello", "code": "print(1)"}' | python3 -m json.tool

test-exercises:
	@echo "Fetching details for ex00_hello..."
	@curl -s http://127.0.0.1:8000/v1/exercises/ex00_hello | python3 -m json.tool

test-grade-docker:
	@echo "Submitting ex01_docker for 'test_user'..."
	@curl -X POST http://127.0.0.1:8000/v1/grade \
		-H "Content-Type: application/json" \
		-d '{"user_id": "test_user", "exercise_id": "ex01_docker", "code": "FROM alpine\nCMD echo hello"}' | python3 -m json.tool

test-leaderboard:
	@echo "Fetching Leaderboard..."
	@curl -s http://127.0.0.1:8000/v1/leaderboard | python3 -m json.tool


