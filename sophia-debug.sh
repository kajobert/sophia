#!/bin/bash
# Sophia AI Debug Launcher (verbose logging)
# Usage: ./sophia-debug.sh --once "Your question"

set -e

# Activate venv if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    source .venv/bin/activate
fi

# Run Sophia with debug flag
python run.py --debug "$@"
