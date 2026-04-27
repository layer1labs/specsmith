#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
[ -f "$VENV_DIR/bin/activate" ] || { echo "ERROR: Run scripts/setup.sh first." >&2; exit 1; }
source "$VENV_DIR/bin/activate"
forge_cli "$@"
