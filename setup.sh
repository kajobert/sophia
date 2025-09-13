#!/bin/bash

# Zastaví provádění skriptu, pokud jakýkoliv příkaz selže
set -e

# Vypíše každý příkaz, který se provádí, pro snadnější ladění
set -x

echo "INFO: Starting Sophia V3 environment setup..."

echo "INFO: Upgrading pip..."
python3 -m pip install --upgrade pip

echo "INFO: Installing dependencies from requirements.txt..."
python3 -m pip install -r requirements.txt

# Vytvoření .env souboru
if [ -f ".env.example" ]; then
    echo "INFO: Found .env.example, copying to .env..."
    cp .env.example .env
else
    echo "WARNING: .env.example not found. Creating an empty .env file."
    echo "INFO: You may need to manually add environment variables to the .env file."
    touch .env
fi

echo "✅ SUCCESS: Environment setup complete."
echo "You can now start the application by running: python3 guardian.py"
