#!/bin/bash
# SOPHIA Factory Reset - Vymazání všech databází, logů a cache
# Použití: ./clean_sophia.sh

set -e

echo "🧹 SOPHIA Factory Reset"
echo "======================="
echo ""

# Stop Guardian if running
echo "⏸️  Stopping Guardian..."
pkill -f "guardian.py" || true
pkill -f "autonomous_main.py" || true
sleep 2

# Backup current state
BACKUP_DIR=".data_backup/before_clean_$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup in $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
if [ -d ".data" ]; then
    cp -r .data/* "$BACKUP_DIR/" 2>/dev/null || true
fi
if [ -d "logs" ]; then
    cp logs/*.log "$BACKUP_DIR/" 2>/dev/null || true
fi

# Clean databases
echo "🗑️  Removing databases..."
rm -f .data/tasks.sqlite
rm -f .data/memory.db
echo "   ✅ Databases deleted"

# Clean logs
echo "🗑️  Removing logs..."
rm -f logs/*.log
echo "   ✅ Logs deleted"

# Clean session cache (if exists)
echo "🗑️  Removing session cache..."
rm -rf .cache/* 2>/dev/null || true
rm -rf __pycache__/* 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Cache cleared"

# Clean autotask results
echo "🗑️  Removing autotask results..."
rm -rf autotask_results/* 2>/dev/null || true
echo "   ✅ Autotask results deleted"

echo ""
echo "✨ SOPHIA reset complete!"
echo "📦 Backup saved to: $BACKUP_DIR"
echo ""
echo "Ready for first awakening. To start SOPHIA:"
echo "  .venv/bin/python guardian.py --worker-script scripts/autonomous_main.py"
echo ""
