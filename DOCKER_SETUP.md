# ZeroOps Workshop - Docker Setup

## Quick Start with Docker

### Build the images:
```bash
make docker-build
```

### Run both server and client:
```bash
make docker-up
```

### Stop everything:
```bash
make docker-down
```

### Run only server:
```bash
make docker-server
```

### Run only client (server must be running):
```bash
make docker-client
```

### View logs:
```bash
make docker-logs
```

## Without Docker

### Start server:
```bash
make run-server
```

### Start client (in another terminal):
```bash
make run-client
```

## Environment Variables

Set your session token:
```bash
export ZEROOPS_SESSION_TOKEN=your-username
```

## What Docker Solves

- **Consistent environment**: Same Python version, same dependencies everywhere
- **No "works on my machine"**: Server runs identically in any terminal
- **Easy setup**: No need to manually install dependencies
- **Isolation**: Client and server in separate containers
