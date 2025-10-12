#!/bin/bash
#
# Nomad Complete Startup Script
# Spustí backend + TUI v oddělených terminálech
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Nomad Complete Startup"
echo "========================="
echo ""

# Ujisti se, že jsme v project root
cd "$PROJECT_ROOT"

# 1. Spusť backend na pozadí
echo "📡 Starting backend..."
bash "$SCRIPT_DIR/start_backend.sh" --background

if [ $? -ne 0 ]; then
    echo "❌ Failed to start backend"
    exit 1
fi

echo ""
echo "✅ Backend is running"
echo ""

# 2. Pauza pro jistotu
sleep 2

# 3. Spusť TUI
echo "🖥️  Starting TUI client..."
echo ""
bash "$SCRIPT_DIR/start_tui.sh"
