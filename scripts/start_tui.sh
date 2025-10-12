#!/bin/bash
#
# Nomad TUI Client Startup Script
# Automaticky připojí TUI klient k backendu
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_URL="${NOMAD_API_URL:-http://localhost:8080}"

echo "🖥️  Nomad TUI Client Startup"
echo "============================"
echo "Project: $PROJECT_ROOT"
echo "Backend: $API_URL"
echo ""

# Přechod do project root
cd "$PROJECT_ROOT"

# Kontrola Python environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in virtual environment"
    echo "   Recommended: source venv/bin/activate"
fi

# Kontrola závislostí
echo "🔍 Checking dependencies..."
python -c "import textual, httpx, websockets" 2>/dev/null || {
    echo "❌ Missing dependencies!"
    echo "   Run: pip install -r requirements.txt"
    exit 1
}
echo "✅ Dependencies OK"

# Kontrola backendu
echo "🔍 Checking backend connection..."
if ! curl -s "$API_URL/api/v1/health/ping" > /dev/null 2>&1; then
    echo "❌ Backend is not responding at $API_URL"
    echo ""
    echo "💡 Start backend first:"
    echo "   ./scripts/start_backend.sh"
    echo ""
    echo "Or run in background:"
    echo "   ./scripts/start_backend.sh --background"
    exit 1
fi
echo "✅ Backend is responsive"

# Spuštění TUI
echo ""
echo "🚀 Starting Nomad TUI Client..."
echo "   Backend: $API_URL"
echo ""
echo "Keybindings:"
echo "   q          - Quit"
echo "   r          - Refresh"
echo "   Tab        - Switch tabs"
echo "   Ctrl+C     - Quit"
echo ""

exec python tui/client.py --api-url "$API_URL"
