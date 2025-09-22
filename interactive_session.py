import asyncio
import os
import uuid
import yaml
import logging
from dotenv import load_dotenv

from core.gemini_llm_adapter import GeminiLLMAdapter
from core.orchestrator import Orchestrator
from agents.planner_agent import PlannerAgent
from core.context import SharedContext

# --- Konfigurace Logování ---
# Nastavíme logování tak, aby se zobrazovaly informace z CrewAI a dalších modulů
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Načtení Konfigurace ---
def load_app_config():
    """Načte konfiguraci z config.yaml."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error("CHYBA: Konfigurační soubor 'config.yaml' nebyl nalezen.")
        return None
    except yaml.YAMLError as e:
        logging.error(f"CHYBA: Chyba při parsování konfiguračního souboru: {e}")
        return None

async def main():
    """
    Hlavní asynchronní funkce pro spuštění interaktivní REPL session.
    """
    print("--- Sophia Interactive Session ---")
    print("Zadejte svůj požadavek, nebo napište 'exit' pro ukončení.")

    # 1. Načtení .env a konfigurace
    load_dotenv()
    config = load_app_config()
    if not config:
        print("Kritická chyba: Nelze načíst konfiguraci. Ukončuji.")
        return

    # 2. Inicializace komponent
    try:
        llm_config = config.get("llm_models", {}).get("primary_llm", {})
        llm_adapter = GeminiLLMAdapter(
            model=llm_config.get("model_name", "gemini-pro"),
            temperature=llm_config.get("temperature", 0.7),
        )
        planner = PlannerAgent(llm=llm_adapter)
        orchestrator = Orchestrator(llm=llm_adapter)
        print("Komponenty (LLM, Planner, Orchestrator) úspěšně inicializovány.")
    except Exception as e:
        print(f"Kritická chyba při inicializaci: {e}")
        return

    # 3. Spuštění REPL smyčky
    while True:
        try:
            prompt = input("\n> ")
            if prompt.lower() in ["exit", "quit", "konec"]:
                print("Ukončuji session. Na shledanou!")
                break
            if not prompt:
                continue

            # --- Fáze 1: Plánování ---
            print("\n--- Fáze 1: Generování plánu... ---")
            session_id = str(uuid.uuid4())
            context = SharedContext(original_prompt=prompt, session_id=session_id)

            # PlannerAgent.run_task je synchronní metoda, která vrací upravený kontext
            context_with_plan = planner.run_task(context)
            plan = context_with_plan.payload.get("plan")

            if not plan:
                print("\nCHYBA: Plánovač selhal a nevytvořil žádný plán.")
                print(f"Zpětná vazba od plánovače: {context_with_plan.feedback}")
                continue

            # Připravíme kontext pro orchestrátor
            context.current_plan = plan
            print(f"Úspěšně vygenerován plán s {len(plan)} kroky.")
            for i, step in enumerate(plan):
                print(f"  Krok {i+1}: {step['description']}")


            # --- Fáze 2: Provedení ---
            print("\n--- Fáze 2: Provádění plánu... ---")
            # Orchestrator.execute_plan je asynchronní metoda
            final_context = await orchestrator.execute_plan(context)


            # --- Fáze 3: Výsledek ---
            print("\n--- Fáze 3: Výsledek provedení ---")
            print(f"Finální status: {final_context.feedback}")

            print("\nHistorie kroků:")
            if not final_context.step_history:
                print("  (žádné kroky nebyly provedeny)")
            else:
                for step in final_context.step_history:
                    status = step.get("output", {}).get("status", "N/A")
                    result = step.get("output", {}).get("result", "")
                    error = step.get("output", {}).get("error", "")
                    print(f"  - Krok: {step['description']}")
                    print(f"    Stav: {status.upper()}")
                    if status == "success":
                        print(f"    Výstup: {result}")
                    elif status == "error":
                        print(f"    Chyba: {error}")

        except KeyboardInterrupt:
            print("\nUkončuji session. Na shledanou!")
            break
        except Exception as e:
            print(f"\nDošlo k neočekávané chybě: {e}")
            logging.exception("Neočekávaná chyba v hlavní smyčce")


if __name__ == "__main__":
    # Spuštění asynchronní hlavní funkce
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")
