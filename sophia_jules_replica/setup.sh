#!/bin/bash
# ==============================================================================
# Instalační a Ověřovací Skript pro Projekt "Sophia Jules Replica"
#
# Tento skript provede základní nastavení prostředí pro spuštění agenta.
# Zastaví provádění, pokud jakýkoliv příkaz selže (set -e).
# ==============================================================================

set -e

echo "--- Zahájení Nastavení Prostředí pro Sophia Jules Replica ---"

# --- Krok 1: Kontrola Požadavků ---
echo "INFO: Kontroluji verzi Pythonu..."
python3 --version

# --- Krok 2: Instalace Závislostí ---
# Vzhledem ke specifikům prostředí instalujeme závislosti přímo.
echo "INFO: Instaluji závislosti ze souboru requirements.in..."
if [ -f "requirements.in" ]; then
    python3 -m pip install -r requirements.in
else
    echo "CHYBA: Soubor requirements.in nebyl nalezen. Ujistěte se, že spouštíte skript z adresáře 'sophia_jules_replica'."
    exit 1
fi

# --- Krok 3: Vytvoření .env Souboru ---
# Tento soubor obsahuje citlivé údaje, jako jsou API klíče.
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "INFO: Nalezen .env.example, kopíruji ho do .env..."
    cp .env.example .env
    echo "AKCE: Prosím, doplňte svůj GOOGLE_API_KEY do souboru .env, pokud chcete agenta spustit v ONLINE režimu."
else
    echo "INFO: Soubor .env již existuje nebo .env.example nebyl nalezen."
fi

# --- Dokončení ---
echo ""
echo "✅ ÚSPĚCH: Nastavení prostředí bylo úspěšně dokončeno."
echo "Nyní můžete agenta spustit pomocí příkazu:"
echo "python3 main.py \"Váš úkol zde\""