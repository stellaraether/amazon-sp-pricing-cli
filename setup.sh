#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing package and dev dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "Setup complete. To activate the environment in the future, run:"
echo "  source .venv/bin/activate"
