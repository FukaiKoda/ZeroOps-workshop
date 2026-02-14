#!/bin/bash
set -e

# Configuration
INSTALL_DIR="$HOME/.local/share/zeroops-client"
BIN_DIR="$HOME/.local/bin"
CLIENT_CONFIG_DIR="$HOME/.config/zeroops"

# Get Project Root (assuming script is in scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLIENT_DIR="$PROJECT_ROOT/client"

echo "Installing ZeroOps Client (Student Mode)..."

# 1. Ask for Server URL
SERVER_URL=${SERVER_URL:-http://10.12.1.1:8000}

# 2. Create/Update Client Config
mkdir -p "$CLIENT_CONFIG_DIR"
cat > "$CLIENT_CONFIG_DIR/client.env" <<EOF
ZEROOPS_SERVER_URL=$SERVER_URL
EOF
echo "Client configured to connect to: $SERVER_URL"

# 3. Resolve Python/Poetry
cd "$CLIENT_DIR"
if ! command -v poetry &> /dev/null; then
    echo "Error: Poetry not found. Please install poetry."
    exit 1
fi

echo "Installing dependencies..."
poetry install

# 4. Install zeroctl wrapper (Client Mode)
echo "Installing zeroctl client wrapper..."
mkdir -p "$BIN_DIR"

# Get Venv Python
VENV_PYTHON="$($(which poetry) env info --path)/bin/python"
MAIN_SCRIPT="$CLIENT_DIR/src/main.py"

cat > "$BIN_DIR/zeroctl" <<EOF
#!/bin/bash
export ZEROOPS_SERVER_URL="$SERVER_URL"
# Also load from config file if exists (python app does this via pydantic, but env var overrides)
exec "$VENV_PYTHON" "$MAIN_SCRIPT" "\$@"
EOF
chmod +x "$BIN_DIR/zeroctl"

echo "------------------------------------------------"
echo "✅ Client Installation Complete!"
echo "------------------------------------------------"
echo "Run 'zeroctl tui' to start the workshop."
echo "------------------------------------------------"
