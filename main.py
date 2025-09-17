import asyncio
import logging
import os
from unittest.mock import patch
from core.orchestrator import AgentOrchestrator
from core.mocks import mock_litellm_completion_handler

# --- Konfigurace Logování ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Simulovaný Uživatelský Vstup ---
# V reálné aplikaci by tento vstup přišel z API, databáze úkolů, atd.
SIMULATED_USER_TASK = "Vytvoř jednoduchou webovou stránku v HTML, která zobrazí nadpis 'Vítejte v Projektu Sophia' a odstavec s textem 'Toto je testovací stránka generovaná umělou inteligencí.' Soubor ulož jako index.html."

async def main():
    """
    Hlavní asynchronní funkce pro spuštění orchestrace agentů.
    """
    logging.info("--- Zahájení nového cyklu zpracování úkolu ---")

    try:
        orchestrator = AgentOrchestrator()
    except Exception as e:
        logging.error(f"Nepodařilo se inicializovat AgentOrchestrator: {e}")
        return

    async def run_orchestration():
        final_context = await orchestrator.run_orchestration(SIMULATED_USER_TASK)
        logging.info("--- Výsledný kontext po dokončení orchestrace ---")
        logging.info(final_context.payload)
        logging.info("-------------------------------------------------")

    if os.getenv('SOPHIA_ENV') == 'test':
        logging.info("Aplikuji monkeypatch pro litellm.completion v testovacím režimu.")
        with patch('litellm.completion', new=mock_litellm_completion_handler):
            await run_orchestration()
    else:
        await run_orchestration()

    logging.info("--- Cyklus zpracování úkolu dokončen ---")


if __name__ == "__main__":
    # Spuštění hlavní asynchronní funkce
    # V Pythonu 3.7+ je `asyncio.run()` preferovaný způsob
    asyncio.run(main())
