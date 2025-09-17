import asyncio
import uuid
import logging
import os
from unittest.mock import patch
from core.context import SharedContext
from core.llm_config import get_llm
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent
from core.mocks import mock_litellm_completion_handler

# --- Konfigurace Logování ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Simulovaný Uživatelský Vstup ---
# V reálné aplikaci by tento vstup přišel z API, databáze úkolů, atd.
SIMULATED_USER_TASK = "Vytvoř jednoduchou webovou stránku v HTML, která zobrazí nadpis 'Vítejte v Projektu Sophia' a odstavec s textem 'Toto je testovací stránka generovaná umělou inteligencí.' Soubor ulož jako index.html."

async def main():
    """
    Hlavní asynchronní funkce pro orchestraci agentů.
    """
    logging.info("--- Zahájení nového cyklu zpracování úkolu ---")

    # 1. Načtení úkolu a vytvoření kontextu
    session_id = str(uuid.uuid4())
    context = SharedContext(
        session_id=session_id,
        original_prompt=SIMULATED_USER_TASK
    )
    logging.info(f"Vytvořen nový kontext pro session: {session_id}")
    logging.info(f"Původní úkol: {context.original_prompt}")

    # 2. Vytvoření instance LLM a agentů
    try:
        llm = get_llm()
        planner = PlannerAgent(llm)
        engineer = EngineerAgent(llm)
        tester = TesterAgent(llm)
        logging.info("Instance LLM a agentů byly úspěšně vytvořeny.")
    except Exception as e:
        logging.error(f"Kritická chyba při inicializaci LLM nebo agentů: {e}")
        return

    # 3. Spuštění řetězce agentů
    async def run_agent_chain():
        try:
            # Krok 1: Plánovač
            logging.info("--- Spouštím Plánovače ---")
            nonlocal context
            context = await asyncio.to_thread(planner.run_task, context)
            logging.info(f"Stav kontextu po Plánovači: {context.payload}")
            if not context.payload.get('plan'):
                logging.error("Plánovač selhal, nevrátil žádný plán. Ukončuji zpracování.")
                return

            # Krok 2: Inženýr
            logging.info("--- Spouštím Inženýra ---")
            context = await asyncio.to_thread(engineer.run_task, context)
            logging.info(f"Stav kontextu po Inženýrovi: {context.payload}")
            if not context.payload.get('code'):
                logging.error("Inženýr selhal, nevrátil žádný kód. Ukončuji zpracování.")
                return

            # Krok 3: Tester
            logging.info("--- Spouštím Testera ---")
            context = await asyncio.to_thread(tester.run_task, context)
            logging.info(f"Stav kontextu po Testerovi: {context.payload}")

        except Exception as e:
            logging.error(f"Došlo k chybě během provádění řetězce agentů: {e}", exc_info=True)

    if os.getenv('SOPHIA_ENV') == 'test':
        logging.info("Aplikuji monkeypatch pro litellm.completion v testovacím režimu.")
        with patch('litellm.completion', new=mock_litellm_completion_handler):
            await run_agent_chain()
    else:
        await run_agent_chain()

    logging.info("--- Cyklus zpracování úkolu dokončen ---")


if __name__ == "__main__":
    # Spuštění hlavní asynchronní funkce
    # V Pythonu 3.7+ je `asyncio.run()` preferovaný způsob
    asyncio.run(main())
