#!/bin/bash
# Instalační skript pro Sophia
set -e

# 1. Vytvoření a aktivace virtuálního prostředí
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# 2. Instalace závislostí
pip install --upgrade pip
pip install -r requirements.txt

# 3. Vytvoření .env šablony, pokud neexistuje
if [ ! -f .env ]; then
  echo "# Přidejte své API klíče a konfigurace sem" > .env
  echo "GOOGLE_API_KEY=vaš_klíč" >> .env
  echo "SERPER_API_KEY=vaš_klíč" >> .env
fi

# 4. První spuštění (test)
echo "\nInstalace dokončena. Pro spuštění použijte:\n"
echo "  source .venv/bin/activate && python main.py"
