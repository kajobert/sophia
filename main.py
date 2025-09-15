import yaml
import time
import os
from datetime import datetime
import asyncio

CONFIG_FILE = "config.yaml"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sophia_main.log")

def ensure_log_dir_exists():
    """Zajistí, že adresář pro logy existuje."""
    os.makedirs(LOG_DIR, exist_ok=True)

def log_message(message):
    """Zaznamená zprávu do hlavního logu Sophie."""
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {message}\n")
    print(message, flush=True)

def load_config():
    """Načte konfiguraci ze souboru config.yaml."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        log_message("Konfigurace úspěšně načtena.")
        return config
    except FileNotFoundError:
        log_message(f"CHYBA: Konfigurační soubor '{CONFIG_FILE}' nebyl nalezen.")
        return None
    except yaml.YAMLError as e:
        log_message(f"CHYBA: Chyba při parsování konfiguračního souboru: {e}")
        return None

from agents.planner_agent import PlannerAgent
from agents.philosopher_agent import PhilosopherAgent
from memory.advanced_memory import AdvancedMemory
from crewai import Task

async def main():
    """Hlavní funkce Sophie, implementující cyklus bdění a spánku."""
    log_message("Jádro Vědomí (main.py) se spouští.")

    config = load_config()
    if not config:
        log_message("Kritická chyba: Nelze načíst konfiguraci. Ukončuji běh.")
        exit(1)

    waking_duration = config.get('lifecycle', {}).get('waking_duration_seconds', 10)
    sleeping_duration = config.get('lifecycle', {}).get('sleeping_duration_seconds', 5)

    log_message("Zahajuji cyklus Bdění a Spánku.")


    from agents.engineer_agent import EngineerAgent
    from agents.tester_agent import TesterAgent
    from agents.aider_agent import AiderAgent

    while True:
        log_message("STAV: Bdění - Kontrola nových úkolů.")
        memory = AdvancedMemory()
        next_task = await memory.get_next_task()

        if next_task:
            log_message(f"Nalezen nový úkol: {next_task['user_input']} (ID: {next_task['chat_id']})")

            # 1. Plánování
            planning_task = Task(
                description=f"Analyze the following user request and create a detailed, step-by-step execution plan. The user's request is: '{next_task['user_input']}'",
                agent=PlannerAgent,
                expected_output="A list of actionable steps to be executed by other agents."
            )
            log_message("Spouštím PlannerAgenta pro vytvoření plánu...")
            try:
                plan = planning_task.execute()
                log_message(f"Plánovač vytvořil plán:\n{plan}")
            except Exception as e:
                log_message(f"CHYBA: Selhání při zpracování úkolu PlannerAgentem: {e}")
                await memory.update_task_status(next_task['chat_id'], "TASK_FAILED")
                memory.close()
                continue

            # 2. Implementace (Engineer nebo AiderAgent podle typu úkolu)
            engineer_result = None
            aider_result = None
            if any(word in next_task['user_input'].lower() for word in ["refaktoruj", "oprav", "vylepši", "refactor", "fix", "improve"]):
                log_message("Detekován úkol pro AiderAgent (refaktorace/oprava/vylepšení)...")
                aider = AiderAgent()
                try:
                    aider_result = aider.propose_change(description=next_task['user_input'])
                    log_message(f"AiderAgent výsledek: {aider_result}")
                except Exception as e:
                    log_message(f"CHYBA: AiderAgent selhal: {e}")
                    await memory.update_task_status(next_task['chat_id'], "TASK_FAILED")
                    memory.close()
                    continue
            else:
                log_message("Spouštím EngineerAgenta pro implementaci...")
                try:
                    engineer_task = Task(
                        description=plan,
                        agent=EngineerAgent,
                        expected_output="Implemented code in sandbox."
                    )
                    engineer_result = engineer_task.execute()
                    log_message(f"EngineerAgent výsledek: {engineer_result}")
                except Exception as e:
                    log_message(f"CHYBA: EngineerAgent selhal: {e}")
                    await memory.update_task_status(next_task['chat_id'], "TASK_FAILED")
                    memory.close()
                    continue

            # 3. Testování
            log_message("Spouštím TesterAgenta...")
            try:
                tester_task = Task(
                    description="Otestuj nově implementovaný/refaktorovaný kód v sandboxu pomocí unit testů.",
                    agent=TesterAgent,
                    expected_output="Výsledek testů."
                )
                test_result = tester_task.execute()
                log_message(f"TesterAgent výsledek: {test_result}")
                if "fail" in str(test_result).lower() or "error" in str(test_result).lower():
                    log_message("Testy selhaly, úkol se vrací k revizi.")
                    await memory.update_task_status(next_task['chat_id'], "TASK_FAILED")
                else:
                    await memory.update_task_status(next_task['chat_id'], "TASK_COMPLETED")
                    log_message(f"Úkol {next_task['chat_id']} byl úspěšně dokončen.")
            except Exception as e:
                log_message(f"CHYBA: TesterAgent selhal: {e}")
                await memory.update_task_status(next_task['chat_id'], "TASK_FAILED")

        else:
            log_message("Žádné nové úkoly ve frontě, odpočívám...")
            await asyncio.sleep(waking_duration)

        memory.close()

        # --- FÁZE SPÁNKU ---
        log_message("STAV: Spánek - Fáze sebereflexe a konsolidace.")
        try:
            memory = AdvancedMemory()
            await memory.add_memory("Waking cycle completed successfully.", "lifecycle_event")
            memory.close()
            log_message("Přidán záznam o konci cyklu do epizodické paměti.")
        except Exception as e:
            log_message(f"CHYBA: Nepodařilo se zapsat do epizodické paměti: {e}")

        reflection_task = Task(
            description=(
                "Read the most recent memories using your tool (defaulting to the last 10). "
                "Generate a concise, one-paragraph summary of the key events and learnings "
                "from the last 'waking' cycle. Focus on distilling insights, not just listing events."
            ),
            agent=PhilosopherAgent,
            expected_output="A single, insightful paragraph summarizing the recent past."
        )
        log_message("Spouštím Filosofa k sebereflexi...")
        try:
            summary = reflection_task.execute()
            log_message(f"DREAMING: {summary}")
        except Exception as e:
            log_message(f"CHYBA: Došlo k chybě během sebereflexe (PhilosopherAgent): {e}")

        await asyncio.sleep(sleeping_duration)

if __name__ == "__main__":
    asyncio.run(main())
