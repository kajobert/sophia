#!/bin/bash
# Autonomous Complex Query Test via HTTP API

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🧪 AUTONOMOUS COMPLEX QUERY TEST"
echo "════════════════════════════════════════════════════════════════════════════════"
echo "⏰ Start: $(date +%H:%M:%S)"
echo ""
echo "📝 Query:"
echo "   Vyhledej aktuální informace o vývoji umělé inteligence v roce 2025"
echo "   a vytvoř mi stručný report se 3 hlavními trendy. Použij webové vyhledávání."
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📤 Sending query to SOPHIA..."
echo ""

# Send query and measure time
START_TIME=$(date +%s)

curl -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Vyhledej aktuální informace o vývoji umělé inteligence v roce 2025 a vytvoř mi stručný report se 3 hlavními trendy. Použij webové vyhledávání.", "session_id": "autonomous-test"}' \
  2>/dev/null | python3 -m json.tool

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "⏰ End: $(date +%H:%M:%S)"
echo "⏱️  Total time: ${ELAPSED}s"
echo "════════════════════════════════════════════════════════════════════════════════"
