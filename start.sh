#!/bin/bash

# Ukončí skript při první chybě
set -e

# Funkce pro úklid (zabije procesy na pozadí) při ukončení skriptu
cleanup() {
    echo -e "\nINFO: Přijat signál k ukončení. Provádím úklid..."
    # Najdeme a zabijeme všechny procesy spuštěné z mcp_servers
    # Použijeme pkill s -f pro porovnání s celým příkazovým řádkem
    pkill -f "python mcp_servers/" || true # || true zabrání chybě, pokud žádný proces neběží
    echo "INFO: Všechny MCP servery byly ukončeny."
    exit 0
}

# Nastaví odchytávání signálů (Ctrl+C, ukončení) a zavolá funkci cleanup
trap cleanup SIGINT SIGTERM

# 1. Spuštění setup.sh
if [ -f "setup.sh" ]; then
    echo "INFO: Spouštím setup.sh pro kontrolu a instalaci závislostí..."
    bash setup.sh
else
    echo "CHYBA: Soubor setup.sh nebyl nalezen."
    exit 1
fi

# 2. Kontrola a nastavení .env souboru
ENV_FILE=".env"
API_KEY_VAR="GEMINI_API_KEY"
API_KEY=""

if [ -f "$ENV_FILE" ]; then
    # Načteme klíč ze souboru, ignorujeme komentáře
    API_KEY=$(grep "^$API_KEY_VAR=" "$ENV_FILE" | cut -d '=' -f2)
fi

# Zkontrolujeme, zda je klíč prázdný nebo placeholder
if [ -z "$API_KEY" ] || [ "$API_KEY" == "VASE_GOOGLE_API_KLIC_ZDE" ]; then
    echo "VAROVÁNÍ: API klíč pro Gemini nebyl nalezen nebo je neplatný."
    read -p "Prosím, vložte svůj platný Gemini API klíč: " USER_API_KEY
    echo "$API_KEY_VAR=$USER_API_KEY" > "$ENV_FILE"
    echo "INFO: API klíč byl uložen do souboru $ENV_FILE."
else
    echo "INFO: Platný API klíč nalezen v souboru .env."
fi

# 3. Spuštění TUI aplikace
# Aplikace sama se postará o inicializaci orchestrátoru a spuštění MCP serverů.
echo "INFO: Spouštím TUI aplikaci... (Pro ukončení stiskněte Ctrl+Q uvnitř aplikace)"
python tui/app.py

# 4. Úklid po normálním ukončení
# Pokud se skript dostane sem, znamená to, že TUI aplikace skončila.
# Funkce cleanup se zavolá díky 'trap' nastavení na konci skriptu.
echo "INFO: TUI aplikace ukončena."
cleanup