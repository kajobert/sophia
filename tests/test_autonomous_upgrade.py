import subprocess
import os
import shutil

# --- Constants ---
SANDBOX_PATH = "sandbox"
TARGET_FILE = "main.py"
SOURCE_FILE_PATH = "main.py"
SANDBOX_FILE_PATH = os.path.join(SANDBOX_PATH, TARGET_FILE)
SCRIPT_TO_RUN = "run_autonomous_upgrade.py"
EXPECTED_CHANGE = "logging.info('--- Autonomous Upgrade v1 ---')"

def test_autonomous_upgrade_script():
    """
    Integrační test pro skript autonomního upgradu.

    Tento test ověřuje celý proces:
    1. Zajišťuje čisté prostředí v sandboxu.
    2. Spustí skript `run_autonomous_upgrade.py`.
    3. Kontroluje, že skript úspěšně proběhl (exit code 0).
    4. Ověřuje, že soubor v sandboxu byl skutečně upraven.
    """
    # --- 1. Setup: Zajištění čistého prostředí ---
    # Zkopírujeme originální main.py do sandboxu, abychom měli jistotu,
    # že test běží vždy se stejným výchozím souborem.
    shutil.copy(SOURCE_FILE_PATH, SANDBOX_FILE_PATH)

    # --- 2. Execution: Spuštění skriptu ---
    result = subprocess.run(
        ["python3", SCRIPT_TO_RUN],
        capture_output=True,
        text=True
    )

    # --- 3. Assertions: Kontrola výsledku skriptu ---

    # Vypíšeme výstup pro snadnější ladění v případě selhání
    print("--- STDOUT ---")
    print(result.stdout)
    print("--- STDERR ---")
    print(result.stderr)

    # Kontrola, že skript neselhal
    assert result.returncode == 0, f"Skript selhal s chybou:\\n{result.stderr}"
    assert "Proces autonomního upgradu dokončen úspěšně" in result.stderr

    # --- 4. Verification: Kontrola finálního stavu souboru ---
    with open(SANDBOX_FILE_PATH, 'r') as f:
        final_content = f.read()

    assert EXPECTED_CHANGE in final_content, "Očekávaná změna nebyla nalezena v cílovém souboru."
