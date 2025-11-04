#!/bin/bash
# Sophia Runner with Live Logging
# Runs Sophia and pipes output to both console and log file for monitoring

set -e

# Default log file
LOG_FILE="/tmp/sophia_live.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Parse arguments
DEBUG_MODE=false
if [[ "$1" == "--debug" ]]; then
    DEBUG_MODE=true
    shift
fi

# Activate venv
if [[ -z "$VIRTUAL_ENV" ]]; then
    source .venv/bin/activate
fi

# Clear old log
> "$LOG_FILE"

echo "🚀 Starting Sophia..."
echo "📝 Log file: $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run Sophia with tee (output to both console and file)
if [ "$DEBUG_MODE" = true ]; then
    python run.py --debug "$@" 2>&1 | tee "$LOG_FILE"
else
    python run.py "$@" 2>&1 | tee "$LOG_FILE"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Sophia finished. Log saved to: $LOG_FILE"
