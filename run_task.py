import os
import sys
from unittest.mock import patch, MagicMock

# Klíčové: Nastavení testovacího režimu PŘED importem jakýchkoliv modulů Sophie.
os.environ["SOPHIA_TEST_MODE"] = "1"
print(f"SOPHIA_TEST_MODE nastaven na: {os.environ.get('SOPHIA_TEST_MODE')}")

import asyncio
from core.orchestrator import Orchestrator
from core.context import SharedContext
from agents.planner_agent import PlannerAgent

try:
    from core.llm_config import llm
except Exception as e:
    print(f"Došlo k chybě při importu z core.llm_config, což je v pořádku, pokud mockujeme litellm. Chyba: {e}")
    llm = None # Zajistíme, že llm existuje, i když selže import

def mock_litellm_completion_handler(model, messages, **kwargs):
    """
    Mock handler pro `litellm.completion`. Nahrazuje skutečné volání API.
    Vrací předpřipravený plán, pokud detekuje prompt pro plánování.
    """
    prompt_text = " ".join([m.get("content", "") for m in messages]).lower()

    # Specifická kontrola pro náš testovací případ
    if "create a detailed, step-by-step plan" in prompt_text and "create a file called mission.txt" in prompt_text:
        print("\n--- MOCK LLM: Intercepted planning request. Returning hardcoded plan. ---\n")

        plan_json = """
        [
            {
                "step_id": 1,
                "description": "Create a new file in the sandbox with the mission statement.",
                "tool_name": "WriteFileTool",
                "parameters": {
                    "file_path": "mission.txt",
                    "content": "The mission of Project Sophia is to build a bridge between human and artificial consciousness."
                }
            }
        ]
        """

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = f"```json\n{plan_json}\n```"
        return mock_response

    print(f"\n--- MOCK LLM: Intercepted an unexpected request for model {model}. Returning generic response. ---\n")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "This is a generic mock response for an unhandled case."
    return mock_response

async def run_single_task(prompt: str):
    print(f"Spouštím úkol s promptem: '{prompt}'")
    print(f"Použitý LLM objekt: {type(llm)}")

    print("\n--- KROK 1: Vytváření plánu ---")
    planner = PlannerAgent(llm=llm)
    initial_context = SharedContext(session_id="cli_task_session", original_prompt=prompt)
    planned_context = await asyncio.to_thread(planner.run_task, initial_context)

    plan = planned_context.payload.get("plan")
    if not plan:
        print("Chyba: Planner nevrátil žádný plán. Výstup z planneru:")
        print(planned_context.payload)
        return

    print(f"Plán úspěšně vytvořen: {plan}")
    context_for_execution = planned_context
    context_for_execution.current_plan = plan

    print("\n--- KROK 2: Spouštění plánu ---")
    orchestrator = Orchestrator(llm=llm)
    final_context = await orchestrator.execute_plan(context_for_execution)

    print("\n--- VÝSLEDEK ÚKOLU ---")
    print(f"Zpětná vazba: {final_context.feedback}")
    if final_context.payload:
        print("Payload:")
        for key, value in final_context.payload.items():
            print(f"  - {key}: {value}")
    print("----------------------")

def main():
    if len(sys.argv) < 2:
        print("Chyba: Zadejte prosím prompt jako argument.")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    # Klíčové: Spouštíme celý proces uvnitř patch kontextu
    with patch('litellm.completion', new=mock_litellm_completion_handler):
        print("--- Mock patch pro 'litellm.completion' je aktivní. ---")
        asyncio.run(run_single_task(prompt))

if __name__ == "__main__":
    main()
