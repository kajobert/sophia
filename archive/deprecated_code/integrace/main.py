import sys
import os
import asyncio
import argparse

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
try:
    from core.orchestrator import JulesOrchestrator
    from core.rich_printer import RichPrinter
except ImportError as e:
    # RichPrinter zde ještě nemusí být dostupný
    print(f"KRITICKÁ CHYBA: Nepodařilo se naimportovat základní moduly z 'core': {e}")
    sys.exit(1)

async def main():
    """
    Hlavní funkce pro jednorázové spuštění agenta s konkrétním úkolem.
    """
    # Konfigurace logování hned na začátku
    RichPrinter.configure_logging(log_dir=os.path.join(project_root, "logs"))

    parser = argparse.ArgumentParser(description="Sophia V2 - Task Runner")
    parser.add_argument("task", type=str, help="Úkol, který má agent provést.")
    parser.add_argument("--session-id", type=str, default=None, help="ID sezení, na které se má navázat.")
    args = parser.parse_args()

    orchestrator = JulesOrchestrator(project_root=project_root)
    try:
        await orchestrator.initialize()

        if not orchestrator.model:
            RichPrinter.error("Agent je v offline režimu. Pro spuštění úkolu je vyžadován platný API klíč.")
            return

        await orchestrator.run(args.task, session_id=args.session_id)

    except Exception as e:
        import traceback
        tb_string = traceback.format_exc()
        RichPrinter.error(f"Došlo k neočekávané kritické chybě: {e}")
        # Log the full traceback to the file for debugging
        RichPrinter._log(logging.CRITICAL, f"NEOČEKÁVANÁ KRITICKÁ CHYBA\n{tb_string}")
        # Also print to console for immediate visibility
        print(tb_string)
    finally:
        await orchestrator.shutdown()
        RichPrinter.info("Běh agenta byl úspěšně ukončen.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Nemusíme zde volat RichPrinter, protože nevíme, v jakém stavu program je.
        # Jednoduchý print je bezpečnější.
        print("\nProgram ukončen uživatelem (KeyboardInterrupt).")