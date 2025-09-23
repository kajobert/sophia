import asyncio
import uuid
import yaml
import logging
from dotenv import load_dotenv

from core.gemini_llm_adapter import GeminiLLMAdapter
from core.context import SharedContext
from core.cognitive_layers import ReptilianBrain, MammalianBrain
from core.neocortex import Neocortex
from core.memory_systems import ShortTermMemory, LongTermMemory

# --- Konfigurace Logování ---
# Nastavíme logování tak, aby se zobrazovaly informace z CrewAI a dalších modulů
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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

        # cognitive layers
        short_term_memory = ShortTermMemory()
        long_term_memory = LongTermMemory()
        reptilian = ReptilianBrain()
        mammalian = MammalianBrain(long_term_memory=long_term_memory)
        neocortex = Neocortex(llm=llm_adapter, short_term_memory=short_term_memory)

        print("Komponenty (LLM, Planner, Cognitive layers) úspěšně inicializovány.")
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

            # --- Fáze 1: Plazí + Savčí + Neokortex pipeline ---
            print("\n--- Fáze: Reptilian -> Mammalian -> Neocortex pipeline... ---")
            session_id = str(uuid.uuid4())
            context = SharedContext(original_prompt=prompt, session_id=session_id)

            # Run pipeline: Reptilian -> Mammalian -> Neocortex
            ctx1 = reptilian.process_input(context)
            ctx2 = mammalian.process_input(ctx1)

            # neocortex.execute_plan is async and returns final context
            final_context = await neocortex.execute_plan(ctx2)

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
