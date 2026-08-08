#!/usr/bin/env bash

set -e

# ==========================================
# ZeroOps Workshop - Client Setup
# ==========================================

SERVER_URL="http://10.12.1.1:8000"

echo "=========================================="
echo "       ZeroOps Workshop Setup"
echo "=========================================="
echo

# ------------------------------------------
# 1. Check Git
# ------------------------------------------
if ! command -v git >/dev/null 2>&1; then
    echo "❌ Git is not installed."
    echo "Please install Git and run this script again."
    exit 1
fi

echo "✅ Git found: $(git --version)"

# ------------------------------------------
# 2. Check Python
# ------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 is not installed."
    echo "Please install Python 3.10+ and run this script again."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# ------------------------------------------
# 3. Check Poetry
# ------------------------------------------
if ! command -v poetry >/dev/null 2>&1; then
    echo
    echo "❌ Poetry is not installed."
    echo
    echo "Please install Poetry first:"
    echo "https://python-poetry.org/docs/"
    echo
    echo "Then run:"
    echo "  ./setup.sh"
    exit 1
fi

echo "✅ Poetry found: $(poetry --version)"

# ------------------------------------------
# 4. Export ZeroOps Server URL
# ------------------------------------------
export ZEROOPS_SERVER_URL="$SERVER_URL"

echo
echo "🌐 ZeroOps Server:"
echo "   $ZEROOPS_SERVER_URL"

# ------------------------------------------
# 5. Install dependencies
# ------------------------------------------
echo
echo "📦 Installing ZeroOps dependencies..."

make install

echo
echo "✅ Dependencies installed successfully."

# ------------------------------------------
# 6. Check server connectivity
# ------------------------------------------
echo
echo "🔍 Checking ZeroOps server..."

if command -v curl >/dev/null 2>&1; then
    if curl -fsS --max-time 5 "$ZEROOPS_SERVER_URL/health" >/dev/null 2>&1; then
        echo "✅ ZeroOps server is reachable."
    else
        echo "⚠️  ZeroOps server is not reachable at:"
        echo "   $ZEROOPS_SERVER_URL"
        echo
        echo "Make sure you are connected to the school network."
        echo "Continuing with the client setup..."
    fi
else
    echo "⚠️  curl is not installed. Skipping server connectivity check."
fi

# ------------------------------------------
# 7. Start ZeroOps
# ------------------------------------------
echo
echo "=========================================="
echo "       ZeroOps is ready!"
echo "=========================================="
echo
echo "Server: $ZEROOPS_SERVER_URL"
echo
echo "Starting ZeroOps Workshop Client..."
echo

make run