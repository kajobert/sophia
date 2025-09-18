import os
import logging
import sys

# --- Konfigurace ---
SANDBOX_PATH = "sandbox"
TARGET_FILE = "main.py"
FULL_PATH = os.path.join(SANDBOX_PATH, TARGET_FILE)
UPGRADE_PROMPT = "Add a log message at the beginning of the main function: logging.info('--- Autonomous Upgrade v1 ---')"
EXPECTED_CHANGE = "logging.info('--- Autonomous Upgrade v1 ---')"

# --- Konfigurace Logování ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def simulate_aider_agent(file_path: str, prompt: str):
    """
    Simuluje akci Aider agenta. Místo volání LLM provede jednoduchou
    úpravu souboru na základě promptu.
    """
    logging.info(f"Simuluji Aider agenta na souboru: {file_path}")
    logging.info(f"Prompt pro úpravu: {prompt}")

    # Jednoduchá implementace, která hledá definici funkce 'main'
    # a vloží za ni logovací hlášku.
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Najdi řádek s 'async def main():'
        main_func_line_index = -1
        for i, line in enumerate(lines):
            if "async def main():" in line:
                main_func_line_index = i
                break

        if main_func_line_index == -1:
            logging.error("Nepodařilo se najít 'async def main():' v cílovém souboru.")
            return False

        # Vlož nový řádek za definici funkce
        # `+ 2` preskočí řádek s definicí a docstring
        insert_index = main_func_line_index + 2
        lines.insert(insert_index, f"    {EXPECTED_CHANGE}\\n")

        with open(file_path, 'w') as f:
            f.writelines(lines)

        logging.info("Soubor byl úspěšně upraven (simulovaně).")
        return True
    except Exception as e:
        logging.error(f"Došlo k chybě při simulované úpravě souboru: {e}")
        return False

def verify_change(file_path: str, expected_content: str) -> bool:
    """
    Ověří, že soubor obsahuje očekávaný obsah.
    """
    logging.info(f"Ověřuji změnu v souboru: {file_path}")
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        if expected_content in content:
            logging.info("Ověření úspěšné: Očekávaný obsah byl nalezen.")
            return True
        else:
            logging.error("Ověření selhalo: Očekávaný obsah nebyl nalezen.")
            return False
    except Exception as e:
        logging.error(f"Došlo k chybě při ověřování souboru: {e}")
        return False


def main():
    """
    Hlavní funkce pro spuštění a orchestraci autonomního upgradu.
    """
    logging.info("--- Zahájení procesu autonomního upgradu ---")

    # Krok 1: Spuštění (simulovaného) agenta pro úpravu kódu
    success = simulate_aider_agent(FULL_PATH, UPGRADE_PROMPT)

    if not success:
        logging.error("Proces autonomního upgradu selhal ve fázi úpravy kódu.")
        sys.exit(1)

    # Krok 2: Ověření změny
    verification_success = verify_change(FULL_PATH, EXPECTED_CHANGE)

    if not verification_success:
        logging.error("Proces autonomního upgradu selhal ve fázi ověření.")
        sys.exit(1)

    logging.info("--- Proces autonomního upgradu dokončen úspěšně ---")


if __name__ == "__main__":
    main()
