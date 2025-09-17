"""
Orchestrátor autonomního vylepšení.
Spustí AiderAgenta s úkolem pro autonomní úpravu kódu v sandboxu.
"""
import os
import sys

# Přidání cesty k `agents` modulu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.aider_agent import AiderAgent

def orchestrate_self_improvement():
    """
    Orchestruje jeden cyklus autonomního vylepšení.
    """
    print("--- Starting Autonomous Self-Improvement Cycle ---")
    try:
        # Načtení úkolu z prompt souboru
        prompt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'self_improve_task_1.txt'))
        with open(prompt_path, 'r') as f:
            task_description = f.read()

        print(f"Loaded task: {task_description.strip()}")

        # Vytvoření instance AiderAgenta
        aider_agent = AiderAgent()

        # Spuštění úlohy
        print("Invoking AiderAgent to propose changes...")
        result = aider_agent.propose_change(description=task_description)

        print(f"AiderAgent finished successfully. Result: {result}")
        print("--- Autonomous Self-Improvement Cycle Finished ---")
        return True

    except FileNotFoundError:
        print(f"Error: Prompt file not found at {prompt_path}")
        return False
    except Exception as e:
        print(f"An error occurred during the self-improvement cycle: {e}")
        return False

if __name__ == "__main__":
    orchestrate_self_improvement()
