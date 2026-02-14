# 🔬 Lab 06: The Bridge
## "Container Communication & Networking"

## 🔑 Core Concepts

- Default `bridge` network and its limitations
- Creating custom bridge networks
- Container DNS (resolving containers by name)
- Network isolation and basic security

## 🧩 Scenario

The Grade Me system is growing:

- A backend API that processes submissions
- A database that stores data

The backend needs to connect to the database, but hardcoding IP addresses is fragile. When containers restart, IPs can change.

Your mission: create a private network where containers can find each other by **name**, like a private phone directory.

## 🎯 Objective

By the end of this lab, you should be able to:

- Create a custom Docker network
- Run multiple containers on the same network
- Use container names as hostnames for communication
- Explain why custom networks are better than the default bridge for real apps

## 📥 Provided

- Docker images: `postgres:15-alpine`, `alpine`

## 🛠️ Task List

### Part A: The Problem (Default Network)

- Run a PostgreSQL container named `db-alone` with `POSTGRES_PASSWORD=test`.
- Run an Alpine container and try to ping `db-alone` by name.
- Observe the failure (the default `bridge` network is the wrong tool here).
- Stop and remove both containers.

### Part B: The Solution (Custom Network)

- Create a custom bridge network called `grademe-network`.
- Verify it exists with `docker network ls`.
- Run a PostgreSQL container:
	- Name: `grademe-db`
	- Network: `grademe-network`
	- Env: `POSTGRES_PASSWORD=secretpass`
- Run an Alpine container on the same network:
	- Name: `grademe-api`
	- Network: `grademe-network`
	- Keep it running with: `sleep 3600`
- From `grademe-api`, ping `grademe-db` by name (check Hints).

### Part C: Test Real Connectivity

- From `grademe-api`, install the PostgreSQL client:

```bash
apk add --no-cache postgresql-client
```

- Connect to the database using the container name as hostname:

```bash
psql -h grademe-db -U postgres
```

- You should get a password prompt. Enter: `secretpass`
- Run `\conninfo` to verify you're connected.
- Exit with `\q`.

Important: Submit/Grade **during Part B/C** (while `grademe-network`, `grademe-db`, and `grademe-api` still exist).

### Part D: Cleanup (after you pass grading)

- Stop and remove both containers.
- Remove the custom network.

## ⚠️ Constraints

- You must create a network named exactly `grademe-network`.
- Do not use `--link` (deprecated).
- Do not use IP addresses for connectivity — use container names only.

## 🧪 Validation

During Part B/C, run:

```bash
docker exec grademe-api ping -c 3 grademe-db
```

Expected output (IP will vary):

```text
PING grademe-db (172.xx.yy.zz): 56 data bytes
64 bytes from 172.xx.yy.zz: seq=0 ttl=64 time=...
64 bytes from 172.xx.yy.zz: seq=1 ttl=64 time=...
64 bytes from 172.xx.yy.zz: seq=2 ttl=64 time=...
```

## 🧠 Hints

- Use `docker run --network=grademe-network` to attach a container to the network.
- Alpine ping syntax: `docker exec <container-name> ping -c 3 hostname`.
- The key learning: **custom bridge networks provide name-based discovery for containers on that network**.

## 📋 Cheat Sheet

### Networks

| Command | What it does |
|---|---|
| `docker network create X` | Creates a private network named `X` |
| `docker network ls` | Lists all networks |
| `docker network inspect X` | Shows which containers are connected |
| `docker network rm X` | Deletes an empty network |

### Connecting containers

| Command | What it does |
|---|---|
| `--network=X` | Starts a container connected to network `X` |
| `docker network connect X <container>` | Adds a running container to `X` |
| `docker network disconnect X <container>` | Removes a container from `X` |

## 🆚 Default Bridge vs Custom Bridge

| Feature | Default bridge | Custom bridge |
|---|---|---|
| DNS resolution by name | ❌ No | ✅ Yes |
| Isolation | ❌ Very weak by default | ✅ Only same-network containers |
| Recommended for | Quick one-off tests | Real applications |
