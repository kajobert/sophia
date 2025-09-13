#!/bin/bash

# Zastaví provádění skriptu, pokud jakýkoliv příkaz selže
set -e

# Vypíše každý příkaz, který se provádí, pro snadnější ladění
set -x

echo "INFO: Creating virtual environment..."
python3 -m venv .venv

echo "INFO: Activating virtual environment..."
source .venv/bin/activate

echo "INFO: Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "INFO: Environment setup complete."
