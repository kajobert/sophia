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
from memory.episodic_memory import EpisodicMemory
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
        log_message("STAV: Bdění - Aktivní fáze.")
        log_message("Simuluji aktivní činnost (placeholder)...")
        # Zde bude v budoucnu probíhat interakce s uživatelem a plnění úkolů
        time.sleep(waking_duration)

        # --- FÁZE SPÁNKU ---
        log_message("STAV: Spánek - Fáze sebereflexe a konsolidace.")

        # 1. Přidáme záznam o dokončení cyklu do epizodické paměti
        try:
            memory = EpisodicMemory()
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
