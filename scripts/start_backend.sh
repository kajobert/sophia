#!/bin/bash
#
# Nomad Backend Startup Script
# Automaticky spustí backend s ochranou proti port conflicts
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT="${NOMAD_PORT:-8080}"
HOST="${NOMAD_HOST:-0.0.0.0}"
LOG_LEVEL="${NOMAD_LOG_LEVEL:-warning}"

echo "🚀 Nomad Backend Startup"
echo "========================"
echo "Project: $PROJECT_ROOT"
echo "Port: $PORT"
echo "Host: $HOST"
echo ""

# Funkce pro zjištění, co běží na portu
check_port() {
    lsof -ti:$PORT 2>/dev/null || true
}

# Ukončení starých procesů
echo "🔍 Checking port $PORT..."
OLD_PIDS=$(check_port)

if [ -n "$OLD_PIDS" ]; then
    echo "⚠️  Port $PORT is already in use by PIDs: $OLD_PIDS"
    echo "🛑 Killing old processes..."
    
    # Pokus o graceful shutdown
    kill $OLD_PIDS 2>/dev/null || true
    sleep 2
    
    # Kontrola, jestli jsou stále živé
    STILL_ALIVE=$(check_port)
    if [ -n "$STILL_ALIVE" ]; then
        echo "⚠️  Processes still alive, forcing kill..."
        kill -9 $STILL_ALIVE 2>/dev/null || true
        sleep 1
    fi
    
    echo "✅ Old processes terminated"
else
    echo "✅ Port $PORT is free"
fi

# Cleanup zombie uvicorn/python procesů
echo "🧹 Cleaning up zombie processes..."
pkill -9 -f "uvicorn.*backend.server" 2>/dev/null || true
pkill -9 -f "python.*backend.server" 2>/dev/null || true
sleep 1

# Přechod do project root
cd "$PROJECT_ROOT"

# Kontrola Python environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in virtual environment"
    echo "   Recommended: source venv/bin/activate"
fi

# Kontrola závislostí
echo "🔍 Checking dependencies..."
python -c "import fastapi, uvicorn, pydantic" 2>/dev/null || {
    echo "❌ Missing dependencies!"
    echo "   Run: pip install -r requirements.txt"
    exit 1
}
echo "✅ Dependencies OK"

# Kontrola Gemini API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY not set"
    echo "   Backend will fail to initialize orchestrator"
fi

# Spuštění backendu
echo ""
echo "🚀 Starting Nomad Backend..."
echo "   URL: http://$HOST:$PORT"
echo "   Docs: http://localhost:$PORT/docs"
echo "   WebSocket: ws://localhost:$PORT/ws"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Spustit s nebo bez background módu
if [ "$1" = "--background" ] || [ "$1" = "-b" ]; then
    # Background mód
    echo "📋 Starting in background mode..."
    
    LOG_FILE="$PROJECT_ROOT/logs/backend_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$PROJECT_ROOT/logs"
    
    nohup python -m uvicorn backend.server:app \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL" \
        > "$LOG_FILE" 2>&1 &
    
    BACKEND_PID=$!
    echo "✅ Backend started with PID: $BACKEND_PID"
    echo "📝 Logs: $LOG_FILE"
    
    # Počkat na startup
    echo "⏳ Waiting for backend to start..."
    for i in {1..10}; do
        sleep 1
        if curl -s http://localhost:$PORT/api/v1/health/ping > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            echo ""
            echo "To stop: kill $BACKEND_PID"
            echo "To view logs: tail -f $LOG_FILE"
            exit 0
        fi
        echo -n "."
    done
    
    echo ""
    echo "⚠️  Backend did not respond within 10 seconds"
    echo "   Check logs: tail -f $LOG_FILE"
    exit 1
else
    # Foreground mód (default)
    exec python -m uvicorn backend.server:app \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL"
fi
