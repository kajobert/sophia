import os
import sys
import logging
import argparse
from unittest.mock import patch

# --- Podmínečné Mockování pro Testovací Prostředí ---
# Tento blok kódu zajišťuje, že pokud je skript spuštěn v testovacím
# prostředí (např. z integračního testu), všechny externí služby
# (jako LLM) jsou správně mockovány.
if os.getenv('SOPHIA_ENV') == 'test':
    # Musíme zajistit, aby se cesta k modulům nastavila i zde
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from core.mocks import mock_litellm_completion_handler

    print("--- LEARNING CYCLE SCRIPT IN TEST MODE: Patching litellm.completion. ---")

    patcher_completion = patch('litellm.completion', new=mock_litellm_completion_handler)
    patcher_acompletion = patch('litellm.acompletion', new=mock_litellm_completion_handler)
    patcher_completion.start()
    patcher_acompletion.start()

from tools.test_runner import run_tests_and_get_results
from agents.debugger_agent import DebuggerAgent

# --- Konfigurace Logování ---
# Nastavíme logování tak, aby šlo do stdout pro snazší zachytávání v testech
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Hlavní funkce pro spuštění cyklu učení z chyb.
    1. Spustí testy (volitelně na konkrétní cestě).
    2. Pokud jsou chyby, předá je DebuggerAgentovi k analýze.
    """
    parser = argparse.ArgumentParser(description="Spustí cyklus učení z chyb v testech.")
    parser.add_argument(
        "--test-path",
        type=str,
        help="Volitelná cesta k testovacímu souboru nebo adresáři."
    )
    args = parser.parse_args()

    logging.info(f"--- Zahájení cyklu učení z chyb v testech (cesta: {args.test_path or 'všechny'}) ---")

    # Krok 1: Spuštění testů a získání výsledků
    test_failures = run_tests_and_get_results(target_path=args.test_path)

    # Zkontrolujeme, zda nedošlo k fatální chybě při spouštění testů
    if test_failures is None:
        logging.error("Nepodařilo se získat výsledky testů. Cyklus učení se přerušuje.")
        sys.exit(1)

    # Krok 2: Analýza výsledků
    if not test_failures:
        logging.info("Všechny testy prošly úspěšně. Není co se učit.")
        return

    logging.warning(f"Detekováno {len(test_failures)} selhání. Spouštím analýzu první chyby.")

    # Krok 3: Spuštění Debugger Agenta pro analýzu první chyby
    first_failure = test_failures[0]

    try:
        debugger = DebuggerAgent()
        analysis = debugger.run_task(first_failure)

        logging.info("--- Analýza od Debugger Agenta ---")
        logging.info(analysis)
        print("\n--- Analýza od Debugger Agenta ---")
        print(analysis)
        logging.info("------------------------------------")

    except Exception as e:
        logging.error(f"Došlo k chybě při spouštění Debugger Agenta: {e}", exc_info=True)
        sys.exit(1)

    logging.info("--- Cyklus učení z chyb dokončen ---")


if __name__ == "__main__":
    main()
