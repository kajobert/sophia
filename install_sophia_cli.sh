#!/bin/bash
# Instalační skript pro SOPHIA CLI aliasy
# Spustit v aktivovaném virtuálním prostředí (venv)

set -e

if [ -z "$VIRTUAL_ENV" ]; then
  echo "[CHYBA] Nejprve aktivujte Python virtuální prostředí (source .venv/bin/activate)"
  exit 1
fi

# Přidat alias pro hlavní dashboard
chmod +x $(pwd)/sophia_cli_dashboard.py
echo "alias sophia='$(pwd)/sophia_cli_dashboard.py'" >> "$VIRTUAL_ENV/bin/activate"
# Přidat alias pro hlavní běh systému
echo "[SOPHIA] Alias 'sophia' a 'sophia-run' byly přidány. Po příští aktivaci venv můžete používat příkazy:"
echo "[SOPHIA] Alias 'sophia' byl přidán. Po příští aktivaci venv můžete používat příkaz:"
echo "  sophia      # Spustí CLI dashboard"
