import os
import sys
import yaml
import asyncio
from unittest.mock import patch, MagicMock

def load_config():
    """Načte a parsuje config.yaml."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Chyba: config.yaml nebyl nalezen.")
        return None
    except yaml.YAMLError as e:
        print(f"Chyba při parsování config.yaml: {e}")
        return None

# --- Mock Handler pro Offline Režim ---
def mock_litellm_completion_handler(model, messages, **kwargs):
    """
    Mock handler pro `litellm.completion`. Vrací předpřipravený plán.
    """
    print("\n--- MOCK LLM: Volání zachyceno, vracím testovací plán pro offline režim. ---\n")

    plan_json = """
    [
        {
            "step_id": 1,
            "description": "Vytvoření testovacího souboru v sandboxu pro offline režim.",
            "tool_name": "WriteFileTool",
            "parameters": {
                "file_path": "offline_test.txt",
                "content": "Offline test byl úspěšný."
            }
        }
    ]
    """

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = f"```json\n{plan_json}\n```"
    return mock_response

async def run_task_logic(prompt: str, mode: str):
    """
    Hlavní logika pro plánování a spuštění úkolu.
    """
    # Importy modulů Sophie až po potenciálním nastavení prostředí
    from core.orchestrator import Orchestrator
    from core.context import SharedContext
    from agents.planner_agent import PlannerAgent
    from core.llm_config import llm

    print(f"Spouštím úkol v '{mode}' režimu s promptem: '{prompt}'")

    if mode == "online" and llm is None:
        print("Chyba: LLM se nepodařilo inicializovat. Zkontrolujte API klíč v .env souboru.")
        return

    print(f"Použitý LLM objekt: {type(llm)}")

    # --- KROK 1: Vytvoření plánu ---
    print(f"\n--- KROK 1: Vytváření plánu ({mode}) ---")
    planner = PlannerAgent(llm=llm)
    initial_context = SharedContext(session_id=f"cli_{mode}_task", original_prompt=prompt)
    planned_context = await asyncio.to_thread(planner.run_task, initial_context)

    plan = planned_context.payload.get("plan")
    if not plan:
        print("Chyba: Planner nevrátil žádný plán.")
        print(f"Výstup z planneru: {planned_context.payload}")
        return

    print(f"Plán úspěšně vytvořen: {plan}")
    context_for_execution = planned_context
    context_for_execution.current_plan = plan

    # --- KROK 2: Spuštění plánu ---
    print(f"\n--- KROK 2: Spouštění plánu ({mode}) ---")
    orchestrator = Orchestrator(llm=llm)
    final_context = await orchestrator.execute_plan(context_for_execution)

    print("\n--- VÝSLEDEK ÚKOLU ---")
    print(f"Zpětná vazba: {final_context.feedback}")

def main():
    """
    Načte konfiguraci a spustí úkol v odpovídajícím režimu.
    """
    config = load_config()
    if not config:
        sys.exit(1)

    mode = config.get("execution_mode", "offline") # Defaultně offline pro bezpečnost

    if len(sys.argv) < 2:
        print("Chyba: Zadejte prosím prompt jako argument v uvozovkách.")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    if mode == "offline":
        os.environ["SOPHIA_TEST_MODE"] = "1"
        print("--- Režim: OFFLINE. Používám mock LLM. ---")
        with patch('litellm.completion', new=mock_litellm_completion_handler):
            asyncio.run(run_task_logic(prompt, mode))
    elif mode == "online":
        print("--- Režim: ONLINE. Používám reálné LLM. ---")
        # Není potřeba nic nastavovat, `core.llm_config` by měl načíst .env soubor
        asyncio.run(run_task_logic(prompt, mode))
    else:
        print(f"Chyba: Neznámý execution_mode v config.yaml: '{mode}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
