#!/bin/bash
 # start_sophia_stack.sh
 # Spustí backend (Flask API) na volném portu a otestuje základní autentizaci a ochranu API.

set -e

cd "$(dirname "$0")/.."

BACKEND_PID=""
BACKEND_PORT=""

function find_free_port {
  local port
  for port in {5001..5099}; do
    if ! lsof -i :$port >/dev/null 2>&1; then
      echo $port
      return
    fi
  done
  echo "Nepodařilo se najít volný port v rozsahu 5001-5099" >&2
  exit 1
}
function cleanup {
  if [ -n "$BACKEND_PID" ]; then
    echo "\nZastavuji backend (PID $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Spustit backend na pozadí
 # Najít volný port
BACKEND_PORT=$(find_free_port)
echo "Použiji port $BACKEND_PORT pro backend."
python3 web/api.py &
BACKEND_PID=$!
PYTHONUNBUFFERED=1 FLASK_RUN_PORT=$BACKEND_PORT python3 web/api.py --port $BACKEND_PORT &
sleep 2

# Test: nepřihlášený uživatel
echo "\nTest 1: /api/me bez přihlášení (očekávám 401)"
curl -s -o /tmp/sophia_me1.json -w "%{http_code}" http://localhost:5001/api/me > /tmp/sophia_me1_code.txt
cat /tmp/sophia_me1.json; echo
curl -s -o /tmp/sophia_me1.json -w "%{http_code}" http://localhost:$BACKEND_PORT/api/me > /tmp/sophia_me1_code.txt

# Test: přihlášení
echo "\nTest 2: /api/login (demo login)"
curl -s -c cookies.txt -b cookies.txt -X POST -H "Content-Type: application/json" -d '{"name": "Test User", "email": "test@example.com"}' http://localhost:5001/api/login

curl -s -c cookies.txt -b cookies.txt -X POST -H "Content-Type: application/json" -d '{"name": "Test User", "email": "test@example.com"}' http://localhost:$BACKEND_PORT/api/login
echo "\nTest 3: /api/me po přihlášení (očekávám 200)"
curl -s -c cookies.txt -b cookies.txt http://localhost:5001/api/me
curl -s -o /tmp/sophia_me2.json -w "%{http_code}" -c cookies.txt -b cookies.txt http://localhost:5001/api/me > /tmp/sophia_me2_code.txt
curl -s -c cookies.txt -b cookies.txt http://localhost:$BACKEND_PORT/api/me

# Test: odhlášení
echo "\nTest 4: /api/logout"
curl -s -X POST -c cookies.txt -b cookies.txt http://localhost:5001/api/logout

curl -s -X POST -c cookies.txt -b cookies.txt http://localhost:$BACKEND_PORT/api/logout
echo "\nTest 5: /api/me po odhlášení (očekávám 401)"
curl -s -o /tmp/sophia_me3.json -w "%{http_code}" -c cookies.txt -b cookies.txt http://localhost:5001/api/me > /tmp/sophia_me3_code.txt
cat /tmp/sophia_me3.json; echo
curl -s -o /tmp/sophia_me3.json -w "%{http_code}" -c cookies.txt -b cookies.txt http://localhost:$BACKEND_PORT/api/me > /tmp/sophia_me3_code.txt

echo "\nHotovo. Backend bude nyní ukončen."
