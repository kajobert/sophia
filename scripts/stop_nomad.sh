#!/bin/bash
#
# Nomad Stop Script
# Bezpečně ukončí všechny Nomad procesy
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${NOMAD_PORT:-8080}"

echo "🛑 Nomad Stop"
echo "============="
echo ""

# Najdi všechny relevantní procesy
echo "🔍 Finding Nomad processes..."

# Backend procesy
BACKEND_PIDS=$(pgrep -f "uvicorn.*backend.server" 2>/dev/null || true)
BACKEND_PIDS="$BACKEND_PIDS $(pgrep -f "python.*backend.server" 2>/dev/null || true)"

# TUI procesy
TUI_PIDS=$(pgrep -f "python.*tui/client.py" 2>/dev/null || true)

# Port-based detection
PORT_PIDS=$(lsof -ti:$PORT 2>/dev/null || true)

# Combine all PIDs (unique)
ALL_PIDS=$(echo "$BACKEND_PIDS $TUI_PIDS $PORT_PIDS" | tr ' ' '\n' | sort -u | tr '\n' ' ')

if [ -z "$ALL_PIDS" ]; then
    echo "✅ No Nomad processes running"
    exit 0
fi

echo "Found PIDs: $ALL_PIDS"
echo ""

# Graceful shutdown
echo "🛑 Sending SIGTERM (graceful shutdown)..."
for pid in $ALL_PIDS; do
    if kill -0 $pid 2>/dev/null; then
        echo "  Stopping PID $pid..."
        kill $pid 2>/dev/null || true
    fi
done

# Čekání na ukončení
echo "⏳ Waiting for processes to terminate..."
sleep 3

# Kontrola zbývajících procesů
REMAINING=$(echo "$ALL_PIDS" | tr ' ' '\n' | while read pid; do
    if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then
        echo $pid
    fi
done)

if [ -n "$REMAINING" ]; then
    echo "⚠️  Some processes still running, forcing kill..."
    for pid in $REMAINING; do
        echo "  Killing PID $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    sleep 1
fi

# Final cleanup
pkill -9 -f "uvicorn.*backend.server" 2>/dev/null || true
pkill -9 -f "python.*tui/client.py" 2>/dev/null || true

# Verify
FINAL_CHECK=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$FINAL_CHECK" ]; then
    echo "⚠️  Port $PORT still in use by PID $FINAL_CHECK"
    kill -9 $FINAL_CHECK 2>/dev/null || true
fi

echo ""
echo "✅ All Nomad processes stopped"
