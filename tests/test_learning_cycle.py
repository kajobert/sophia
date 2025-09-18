import subprocess
import os
import sys

# --- Constants ---
TEMP_TEST_FILENAME = "tests/temp_test_for_learning.py"
SCRIPT_TO_RUN = "run_learning_cycle.py"

# The content of the deliberately broken test file
BROKEN_TEST_CONTENT = """
import pytest

def test_always_fails():
    assert False, "This test is designed to fail for the learning cycle."
"""

def test_learning_cycle_with_isolated_failure():
    """
    Integrační test pro skript cyklu učení.

    Tento test ověřuje celý proces v izolovaném prostředí:
    1. Vytvoří dočasný, rozbitý testovací soubor.
    2. Spustí skript `run_learning_cycle.py` a řekne mu, aby spustil testy POUZE na tomto souboru.
    3. Kontroluje, že skript detekoval chybu a zavolal DebuggerAgenta.
    4. Obnoví původní stav (smaže dočasný soubor).
    """
    try:
        # --- 1. Setup: Vytvoření dočasného, rozbitého testu ---
        print(f"\\n--- SETUP: Creating broken test file: {TEMP_TEST_FILENAME} ---")
        with open(TEMP_TEST_FILENAME, "w") as f:
            f.write(BROKEN_TEST_CONTENT)

        # --- 2. Execution: Spuštění skriptu na konkrétním souboru ---
        command = [sys.executable, SCRIPT_TO_RUN, "--test-path", TEMP_TEST_FILENAME]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120
        )

        # --- 3. Assertions: Kontrola výsledku skriptu ---
        print(f"--- STDOUT ---\\n{result.stdout}")
        print(f"--- STDERR ---\\n{result.stderr}")

        assert result.returncode == 0
        assert f"cesta: {TEMP_TEST_FILENAME}" in result.stdout
        assert "Detekováno 1 selhání." in result.stdout
        assert "Spouštím analýzu první chyby." in result.stdout
        assert "Analýza od Debugger Agenta" in result.stdout
        assert "Hypotéza: Chyba je pravděpodobně v asertaci." in result.stdout

    finally:
        # --- 4. Teardown: Smazání dočasného souboru ---
        if os.path.exists(TEMP_TEST_FILENAME):
            print(f"\\n--- TEARDOWN: Removing broken test file: {TEMP_TEST_FILENAME} ---")
            os.remove(TEMP_TEST_FILENAME)
