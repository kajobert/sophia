#!/bin/bash
# Sophia Watch - Real-time monitoring helper
# Shows Sophia's output in real-time with auto-refresh

LOG_FILE="${1:-/tmp/sophia_live.log}"

echo "🔍 Watching Sophia output: $LOG_FILE"
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create log file if doesn't exist
touch "$LOG_FILE"

# Watch with tail -f (real-time updates)
tail -f "$LOG_FILE"
