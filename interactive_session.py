import asyncio
import logging
from core.context import SharedContext
from core.orchestrator import Orchestrator
from agents.custom_planner import CustomPlanner
from core.llm_config import llm

# Základní nastavení logování pro přehlednost
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

class InteractiveSession:
    """
    Třída pro vedení interaktivní session se Sophií z příkazové řádky.
    """

    def __init__(self):
        # Inicializace klíčových komponent
        if llm is None:
            raise ValueError("LLM není k dispozici. Zkontrolujte konfiguraci a .env soubor.")

        self.planner = CustomPlanner(llm=llm)
        self.orchestrator = Orchestrator(llm=llm)
        print("Komponenty (LLM, Planner, Orchestrator) úspěšně inicializovány.\n")

    async def _execute_turn(self, user_prompt: str):
        """
        Zpracuje jeden "tah" konverzace: naplánuje a provede úkol.
        """
        context = SharedContext(session_id="interactive_session", original_prompt=user_prompt)

        # --- Fáze 1: Plánování ---
        print("--- Fáze 1: Generování plánu... ---")
        context = await self.planner.generate_plan(context)
        plan = context.payload.get('plan')

        if not plan:
            print(f"\nCHYBA: Plánovač selhal a nevytvořil žádný plán.")
            print(f"Zpětná vazba od plánovače: {context.feedback}")
            return

        print(f"Úspěšně vygenerován plán s {len(plan)} kroky.")
        for i, step in enumerate(plan):
            print(f"  Krok {i+1}: {step.get('description')}")

        # --- Fáze 2: Provádění ---
        print("\n--- Fáze 2: Provádění plánu... ---")
        context.current_plan = plan
        final_context = await self.orchestrator.execute_plan(context)

        # --- Fáze 3: Výsledek ---
        print("\n--- Fáze 3: Výsledek provedení ---")
        print(f"Finální status: {final_context.feedback}")
        print("\nHistorie kroků:")
        for step in final_context.step_history:
            status = step.get('output', {}).get('status', 'UNKNOWN').upper()
            print(f"  - Krok: {step.get('description')}")
            print(f"    Stav: {status}")
            if status == 'ERROR':
                print(f"    Chyba: {step.get('output', {}).get('error')}")
            else:
                print(f"    Výstup: {step.get('output', {}).get('result')}")


    async def run(self):
        """
        Hlavní smyčka pro interaktivní session.
        """
        print("--- Sophia Interactive Session ---")
        print("Zadejte svůj požadavek, nebo napište 'exit' pro ukončení.")

        while True:
            try:
                user_prompt = await asyncio.to_thread(input, "\n> ")
                if user_prompt.lower() == 'exit':
                    print("Ukončuji session. Na shledanou.")
                    break
                if not user_prompt:
                    continue

                await self._execute_turn(user_prompt)

            except (KeyboardInterrupt, EOFError):
                print("\nUkončuji session. Na shledanou.")
                break
            except Exception as e:
                print(f"\nDošlo k neočekávané chybě: {e}")
                logging.exception("Unexpected error in interactive session")


if __name__ == "__main__":
    import os
    import sys

    # Spuštění v online režimu, vyžaduje .env soubor
    if os.getenv("SOPHIA_TEST_MODE") == "1":
        print("Tento skript je určen pro online režim. Prosím, nespouštějte v SOPHIA_TEST_MODE=1.")
        sys.exit(1)

    try:
        session = InteractiveSession()
        asyncio.run(session.run())
    except ValueError as e:
        print(f"Chyba při inicializaci: {e}")
        sys.exit(1)
