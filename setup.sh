#!/bin/bash

# Tento skript provede základní nastavení vývojového prostředí pro projekt Sophia.
# Zastaví provádění, pokud jakýkoliv příkaz selže.
set -e

echo "--- Starting Sophia Environment Setup ---"

# 1. Kontrola verze Pythonu
echo "INFO: Checking Python version..."
python3 --version
# Zde by mohla být přidána kontrola na minimální verzi, např. 3.12

# 2. Vytvoření virtuálního prostředí
if [ ! -d ".venv" ]; then
    echo "INFO: Creating Python virtual environment in .venv..."
    python3 -m venv .venv
else
    echo "INFO: Virtual environment .venv already exists."
fi

# 3. Aktivace virtuálního prostředí
echo "INFO: Activating virtual environment..."
source .venv/bin/activate

# 4. Instalace závislostí
echo "INFO: Installing dependencies from requirements.txt..."
echo "TIP: For a much faster installation, consider using 'uv'. Install it with 'pip install uv' and then run 'uv pip install -r requirements.txt'."
pip install -r requirements.txt

# 5. Vytvoření .env souboru z příkladu
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "INFO: Found .env.example, copying to .env..."
    cp .env.example .env
    echo "ACTION: Please fill in your GEMINI_API_KEY in the .env file."
else
    echo "INFO: .env file already exists or .env.example not found."
fi

# 6. Spuštění ověřovacích testů
echo "--- Running Verification Tests ---"
echo "INFO: This will verify that the environment is set up correctly."
PYTHONPATH=. pytest

echo ""
echo "✅ SUCCESS: Environment setup complete."
echo "You can now explore the project. See README.md for guidance on where to start."
