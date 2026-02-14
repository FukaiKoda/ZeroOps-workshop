#!/bin/bash
set -e

# Configuration
SERVICE_NAME="zeroops.service"
INSTALL_DIR="$HOME/.local/share/zeroops"
CONFIG_DIR="$HOME/.config/zeroops"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_DIR="$HOME/.config/systemd/user"

# Get Project Root (assuming script is in scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$PROJECT_ROOT/server"

echo "Installing ZeroOps Daemon..."

# 1. Create Directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$SYSTEMD_DIR"

# 2. Generate config if not exists
if [ ! -f "$CONFIG_DIR/server.yaml" ]; then
    echo "Creating default configuration..."
    # Detect IP
    HOST_IP=$(hostname -I | cut -d' ' -f1)
    cat > "$CONFIG_DIR/server.yaml" <<EOF
HOST: 0.0.0.0
PORT: 8000
DEBUG: true
PUBLIC_URL: http://$HOST_IP:8000
EOF
    echo "Configured PUBLIC_URL to http://$HOST_IP:8000"
else
    echo "Configuration already exists."
fi

# 3. Resolve Python/Poetry
cd "$SERVER_DIR"
if command -v poetry &> /dev/null; then
    POETRY_CMD=$(which poetry)
    # Convert poetry env path to explicit uvicorn path
    VENV_ROOT=$($POETRY_CMD env info --path)
    UVICORN_CMD="$VENV_ROOT/bin/uvicorn"
    VENV_PYTHON="$VENV_ROOT/bin/python"
else
    echo "Error: Poetry not found. Please install poetry."
    exit 1
fi

# 3.5 Symlink Exercises (so updates in repo are reflected)
echo "Linking exercises..."
rm -rf "$INSTALL_DIR/exercises"
ln -sf "$PROJECT_ROOT/data/exercises" "$INSTALL_DIR/exercises"

# 4. Create Service File
echo "Generating systemd service unit..."
TEMPLATE_PATH="$PROJECT_ROOT/scripts/templates/zeroops.service"
SERVICE_PATH="$SYSTEMD_DIR/$SERVICE_NAME"

sed -e "s|{{WORKING_DIRECTORY}}|$SERVER_DIR|g" \
    -e "s|{{UVICORN_CMD}}|$UVICORN_CMD|g" \
    "$TEMPLATE_PATH" > "$SERVICE_PATH"

# 5. Reload Systemd and Enable
echo "Enabling service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

# 6. Install zeroctl CLI
echo "Installing zeroctl..."
CLI_SCRIPT="$SERVER_DIR/src/cli.py"
chmod +x "$CLI_SCRIPT"

# Create Wrapper (Use VENV_PYTHON from earlier step)
cat > "$BIN_DIR/zeroctl" <<EOF
#!/bin/bash
exec "$VENV_PYTHON" "$CLI_SCRIPT" "\$@"
EOF
chmod +x "$BIN_DIR/zeroctl"

echo "------------------------------------------------"
echo "✅ Installation Complete!"
echo "------------------------------------------------"
echo "You can now use 'zeroctl' to manage the service."
echo "Try: zeroctl status"
echo "     zeroctl ui"
echo "------------------------------------------------"
