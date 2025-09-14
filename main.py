import yaml
import time
import os
from datetime import datetime

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
    print(message, flush=True) # Přidán flush=True

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

def main():
    """Hlavní funkce Sophie, implementující cyklus bdění a spánku."""
    log_message("Jádro Vědomí (main.py) se spouští.")

    config = load_config()
    if not config:
        log_message("Kritická chyba: Nelze načíst konfiguraci. Ukončuji běh.")
        exit(1)

    waking_duration = config.get('lifecycle', {}).get('waking_duration_seconds', 10)
    sleeping_duration = config.get('lifecycle', {}).get('sleeping_duration_seconds', 5)

    log_message("Zahajuji cyklus Bdění a Spánku.")

    while True:
        # --- FÁZE BDĚNÍ ---
        log_message("STAV: Bdění - Kontrola nových úkolů.")
        memory = AdvancedMemory()
        next_task = memory.get_next_task()

        if next_task:
            log_message(f"Nalezen nový úkol: {next_task['user_input']} (ID: {next_task['chat_id']})")

            # Vytvoření plánovacího úkolu pro PlannerAgenta
            planning_task = Task(
                description=f"Analyze the following user request and create a detailed, step-by-step execution plan. The user's request is: '{next_task['user_input']}'",
                agent=PlannerAgent,
                expected_output="A list of actionable steps to be executed by other agents."
            )

            log_message("Spouštím PlannerAgenta pro vytvoření plánu...")
            try:
                plan = planning_task.execute()
                log_message(f"Plánovač vytvořil plán:\n{plan}")

                # Po úspěšném naplánování označíme úkol jako dokončený
                memory.update_task_status(next_task['chat_id'], "TASK_COMPLETED")
                log_message(f"Úkol {next_task['chat_id']} byl úspěšně naplánován a označen jako dokončený.")

            except Exception as e:
                log_message(f"CHYBA: Selhání při zpracování úkolu PlannerAgentem: {e}")
                # Volitelně můžete vrátit úkol zpět do fronty nebo ho označit jako selhaný
                memory.update_task_status(next_task['chat_id'], "TASK_FAILED")

        else:
            log_message("Žádné nové úkoly ve frontě, odpočívám...")
            time.sleep(waking_duration)

        memory.close()

        # --- FÁZE SPÁNKU ---
        log_message("STAV: Spánek - Fáze sebereflexe a konsolidace.")

        # 1. Přidáme záznam o dokončení cyklu do epizodické paměti
        try:
            memory = AdvancedMemory()
            memory.add_memory("Waking cycle completed successfully.", "lifecycle_event")
            memory.close()
            log_message("Přidán záznam o konci cyklu do epizodické paměti.")
        except Exception as e:
            log_message(f"CHYBA: Nepodařilo se zapsat do epizodické paměti: {e}")

        # 2. Vytvoříme úkol pro Filosofa
        reflection_task = Task(
            description=(
                "Read the most recent memories using your tool (defaulting to the last 10). "
                "Generate a concise, one-paragraph summary of the key events and learnings "
                "from the last 'waking' cycle. Focus on distilling insights, not just listing events."
            ),
            agent=PhilosopherAgent,
            expected_output="A single, insightful paragraph summarizing the recent past."
        )

        # 3. Spustíme Filosofa, aby provedl sebereflexi
        log_message("Spouštím Filosofa k sebereflexi...")
        try:
            summary = reflection_task.execute()
            log_message(f"DREAMING: {summary}")
        except Exception as e:
            log_message(f"CHYBA: Došlo k chybě během sebereflexe (PhilosopherAgent): {e}")

        time.sleep(sleeping_duration)

if __name__ == "__main__":
    main()
