# ZeroOps Service & ZeroCTL

The **Service Layer** binds the Client and Server together into a usable platform. It uses `systemd` to manage the background server process and `zeroctl` to control it.

## 1. ZeroCTL (`zeroctl`)

The unified command-line interface. It is a Python script using `Typer`, installed as a wrapper in `~/.local/bin/zeroctl`.

### Commands

| Command | Description |
| :--- | :--- |
| `zeroctl start` | Starts the `zeroops.service` daemon. |
| `zeroctl stop` | Stops the daemon. |
| `zeroctl restart` | Restarts the daemon. |
| `zeroctl status` | Shows `systemd` status (active/inactive). |
| `zeroctl logs [-f]` | Tails the service logs via `journalctl`. |
| `zeroctl ui` | Launches the TUI Client. |

## 2. Systemd Daemon (`zeroops.service`)

A **User Service** (`systemd --user`) that manages the FastAPI server.
-   **Unit File**: `~/.config/systemd/user/zeroops.service`
-   **Type**: Simple
-   **Autostart**: Enabled by default.

It ensures the server is always running in the background without blocking a terminal.

## 3. Installation Architecture

The system supports a **Distributed Deployment** (Host vs Student).

### Host Installation (Server)
Run `scripts/install_server.sh`. This:
1.  Installs the `zeroops.service` unit.
2.  Links `data/exercises` to `~/.local/share/zeroops/exercises`.
3.  Configures `zeroctl` to manage the daemon.
4.  Generates a config file with `PUBLIC_URL` set to the host's IP.

### Student Installation (Client)
Run `scripts/install_client.sh`. This:
1.  Prompts for the **Server URL**.
2.  Creates a client-specific configuration at `~/.config/zeroops/client.env`.
3.  Installs `zeroctl` as a lightweight wrapper for the TUI.

### Role Switching

> [!WARNING]
> **Important**: Running `install_client.sh` overwrites `zeroctl` with a client-only version.
> - **Host Mode**: `zeroctl` has `start`, `stop`, `logs`, `ui`.
> - **Student Mode**: `zeroctl` only launches the UI (or shows client help).

If you accidentally ran the wrong installer, just re-run the correct one to restore functionality.

### Installation Steps

To deploy the service:

```bash
# 1. Install dependencies
cd server && poetry install
cd client && poetry install

# 2. Run the installer (choose one)
./scripts/install_server.sh  # On Host (Full Admin)
# OR
./scripts/install_client.sh  # On Student (Client Only)
```
