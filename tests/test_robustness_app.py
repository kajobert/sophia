# Tento soubor slouží pouze k otestování chybějícího .env v izolovaném procesu.
# Importuje pouze konfiguraci Sophia, což by mělo selhat pokud .env chybí.

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import core.config  # Tento import by měl selhat při chybějícím .env
except SystemExit as e:
    # Pokud dojde k SystemExit (např. sys.exit()), vypíšeme chybovou hlášku
    print(".env soubor nebyl nalezen")
    raise
except Exception as ex:
    print(f"Neočekávaná výjimka: {ex}")
    raise
