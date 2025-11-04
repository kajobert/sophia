#!/bin/bash
# Quick offline mode launcher for Sophia
# Uses local Llama 3.1 8B only (no cloud fallback)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
source .venv/bin/activate

# Run in offline mode
echo "🔒 Launching Sophia in OFFLINE MODE (local Llama 3.1 8B only)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python run.py --offline "$@"
