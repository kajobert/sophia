#!/bin/bash

# ==============================================================================
# Bootstrap Skript pro Vývojové Prostředí Projektu Sophia
#
# Tento skript zajišťuje konzistentní a funkční prostředí pro AI agenty,
# ať už běží v sandboxu, GitHub Codespace, nebo jiném prostředí.
# Zastaví provádění, pokud jakýkoliv příkaz selže (set -e).
#
# Použití:
#   bash bootstrap_environment.sh
# ==============================================================================

set -e

echo "--- [BOOTSTRAP] Zahájení přípravy prostředí ---"

# --- Krok 1: Kontrola Klíčových Nástrojů ---
echo "INFO: Kontroluji verze klíčových nástrojů..."
python3 --version
uv --version || { echo "VAROVÁNÍ: 'uv' nenalezen. Instalace bude pomalejší."; }
node --version || { echo "VAROVÁNÍ: 'node' nenalezen. Některé webové funkce nemusí být dostupné."; }
echo "-----------------------------------------"

# --- Krok 2: Vytvoření a Aktivace Virtuálního Prostředí ---
# Zajišťuje izolaci závislostí.
if [ ! -d ".venv" ]; then
    echo "INFO: Vytvářím virtuální prostředí v adresáři .venv..."
    python3 -m venv .venv
else
    echo "INFO: Virtuální prostředí .venv již existuje."
fi
echo "INFO: Aktivuji virtuální prostředí..."
source .venv/bin/activate
echo "-----------------------------------------"

# --- Krok 3: Instalace Python Závislostí ---
# Používá 'uv' pro rychlou instalaci, pokud je k dispozici.
# Instaluje ze souboru 'requirements.in', aby byly vždy použity nejnovější
# kompatibilní verze.
echo "INFO: Instaluji Python závislosti ze souboru requirements.in..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.in
else
    pip install -r requirements.in
fi
echo "--------------------------------------------"

# --- Krok 4: Spuštění Ověřovacích Testů ---
# Kritický krok pro ověření, že je prostředí správně nastaveno
# a všechny klíčové komponenty fungují, jak mají.
echo ""
echo "--- [BOOTSTRAP] Spouštím ověřovací testy ---"
PYTHONPATH=. pytest
echo "---------------------------------------------"

echo ""
echo "✅ [BOOTSTRAP] Prostředí je úspěšně připraveno a ověřeno!"
echo "Můžete bezpečně pokračovat v práci."