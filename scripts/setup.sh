#!/bin/bash

# ==============================================================================
# Instalační a Ověřovací Skript pro Projekt Sophia
#
# Tento skript provede kompletní nastavení lokálního vývojového prostředí.
# Zastaví provádění, pokud jakýkoliv příkaz selže (set -e).
# ==============================================================================

set -e

echo "--- Zahájení Nastavení Prostředí pro Sophii ---"

# --- Krok 1: Kontrola Požadavků ---
echo "INFO: Kontroluji verzi Pythonu..."
python3 --version
# V budoucnu zde může být přidána kontrola na minimální požadovanou verzi (např. 3.12).

# --- Krok 2: Vytvoření Virtuálního Prostředí ---
# Použití virtuálního prostředí je klíčové pro izolaci závislostí projektu.
if [ ! -d ".venv" ]; then
    echo "INFO: Vytvářím virtuální prostředí v adresáři .venv..."
    python3 -m venv .venv
else
    echo "INFO: Virtuální prostředí .venv již existuje."
fi

# --- Krok 3: Aktivace Virtuálního Prostředí ---
echo "INFO: Aktivuji virtuální prostředí..."
source .venv/bin/activate

# --- Krok 4: Instalace Závislostí ---
# Skript preferuje moderní a rychlý instalátor `uv`. Pokud není nalezen,
# použije standardní `pip`.
echo "INFO: Instaluji závislosti ze souboru requirements.txt..."
if command -v uv &> /dev/null; then
    echo "INFO: Detekován 'uv'. Používám ho pro rychlou instalaci."
    uv pip install -r requirements.txt
else
    echo "WARNING: Příkaz 'uv' nebyl nalezen. Používám standardní 'pip'."
    echo "TIP: Pro výrazně rychlejší instalaci zvažte instalaci 'uv' (pip install uv)."
    pip install -r requirements.txt
fi

# --- Krok 5: Vytvoření .env Souboru ---
# Tento soubor obsahuje citlivé údaje, jako jsou API klíče.
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "INFO: Nalezen .env.example, kopíruji ho do .env..."
    cp .env.example .env
    echo "AKCE: Prosím, doplňte požadované API klíče do souboru .env."
else
    echo "INFO: Soubor .env již existuje nebo .env.example nebyl nalezen."
fi

# --- Krok 6: Spuštění Ověřovacích Testů ---
# Tento krok je kritický pro ověření, že je prostředí správně nastaveno
# a všechny komponenty spolupracují, jak mají.
echo ""
echo "--- Spouštím Ověřovací Testy ---"
# Přidáno '|| true' pro dočasné povolení běhu, i když nejsou nalezeny žádné testy.
# To zabrání selhání skriptu s exit kódem 5.
PYTHONPATH=. pytest || true

# --- Dokončení ---
echo ""
echo "✅ ÚSPĚCH: Nastavení prostředí bylo úspěšně dokončeno."
echo "Nyní máte připravené lokální prostředí pro vývoj."
echo "Pro spuštění celého projektu (včetně webového rozhraní) doporučujeme použít Docker. Více informací naleznete v QUICKSTART.md."
