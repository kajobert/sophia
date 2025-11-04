#!/bin/bash
# Debug offline mode launcher - shows all logs
# For development and troubleshooting

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv
source .venv/bin/activate

# Run in offline + debug mode
echo "🐛 Launching Sophia in OFFLINE + DEBUG MODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python run.py --debug --offline "$@"
