#!/bin/bash
# Sophia AI Quick Launcher
# Usage: ./sophia.sh [options] "Your question"

set -e

# Activate venv if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    source .venv/bin/activate
fi

# Run Sophia
python run.py "$@"
