#!/bin/bash
#
# Sophia Chat Backend Startup Script
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${SOPHIA_PORT:-8080}"
HOST="${SOPHIA_HOST:-0.0.0.0}"
LOG_LEVEL="${SOPHIA_LOG_LEVEL:-info}"

echo "🚀 Sophia Chat Backend Startup"
echo "============================="
echo "Project: $PROJECT_ROOT"
echo "Port: $PORT"
echo "Host: $HOST"
echo ""

# Change to the project root directory
cd "$PROJECT_ROOT"

# Start the backend
echo "🚀 Starting Sophia Chat Backend..."
echo "   URL: http://$HOST:$PORT"
echo "   Docs: http://localhost:$PORT/docs"
echo "   WebSocket: ws://localhost:$PORT/ws/{session_id}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

exec uvicorn backend.server:app \
    --host "$HOST" \
    --port "$PORT" \
    --log-level "$LOG_LEVEL" \
    --reload
