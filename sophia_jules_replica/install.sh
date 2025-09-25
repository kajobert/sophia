#!/bin/bash
# ==============================================================================
# Interaktivní Instalační Skript pro Projekt "Sophia Jules Replica"
#
# Tento skript provede kompletní nastavení prostředí včetně konfigurace
# API klíče.
# ==============================================================================

set -e

echo "--- Zahájení Interaktivní Instalace ---"

# --- Krok 1: Spuštění základního setupu ---
# Tím zajistíme, že jsou nainstalovány všechny závislosti a existuje .env.example
echo "INFO: Spouštím základní nastavení (setup.sh)..."
if [ ! -f "setup.sh" ]; then
    echo "CHYBA: setup.sh nenalezen. Ujistěte se, že spouštíte tento skript z adresáře 'sophia_jules_replica'."
    exit 1
fi
./setup.sh

# --- Krok 2: Získání API klíče od uživatele ---
echo ""
echo "-----------------------------------------------------"
echo "Nyní je potřeba nastavit Váš Google API klíč."
echo "Tento klíč je nutný pro ONLINE režim agenta."
# Použití -s pro skrytý vstup (silent)
read -s -p "Vložte svůj GOOGLE_API_KEY a stiskněte Enter: " user_api_key
echo "" # Nový řádek pro lepší formátování

if [ -z "$user_api_key" ]; then
    echo "VAROVÁNÍ: Nebyl zadán žádný API klíč."
    echo "Agent bude fungovat pouze v OFFLINE režimu. Klíč můžete přidat později ručně do souboru .env."
else
    echo "INFO: Ukládám API klíč do souboru .env..."
    # Přepíše .env soubor s novým klíčem
    echo "GOOGLE_API_KEY=\"$user_api_key\"" > .env
    echo "INFO: API klíč byl úspěšně uložen."
fi

# --- Dokončení ---
echo ""
echo "✅ ÚSPĚCH: Instalace a konfigurace byly úspěšně dokončeny."
echo "Nyní můžete agenta spustit pomocí příkazu:"
echo "python3 main.py \"Váš úkol zde\""