from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
from datetime import datetime
import yaml

from agents.philosopher_agent import PhilosopherAgent
from core.context import SharedContext
from core.orchestrator import Orchestrator
from core.gemini_llm_adapter import GeminiLLMAdapter
from crewai import Task
from memory.advanced_memory import AdvancedMemory


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
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
        log_message("Konfigurace úspěšně načtena.")
        return config
    except FileNotFoundError:
        log_message(f"CHYBA: Konfigurační soubor '{CONFIG_FILE}' nebyl nalezen.")
        return None
    except yaml.YAMLError as e:
        log_message(f"CHYBA: Chyba při parsování konfiguračního souboru: {e}")
        return None


async def main():
    """Hlavní funkce Sophie, implementující cyklus bdění a spánku."""
    log_message("Jádro Vědomí (main.py) se spouští.")

    config = load_config()
    if not config:
        log_message("Kritická chyba: Nelze načíst konfiguraci. Ukončuji běh.")
        exit(1)

    # Načtení konfigurace LLM a vytvoření instance
    llm_config = config.get("llm_models", {}).get("primary_llm", {})
    if not llm_config:
        log_message("Kritická chyba: Konfigurace pro primární LLM nebyla nalezena.")
        exit(1)

    try:
        llm = GeminiLLMAdapter(
            model=llm_config.get("model_name", "gemini-pro"),
            temperature=llm_config.get("temperature", 0.7),
        )
        log_message(f"LLM Adapter pro model {llm.model_name} úspěšně vytvořen.")
    except Exception as e:
        log_message(f"Kritická chyba: Nepodařilo se vytvořit LLM adapter: {e}")
        exit(1)

    waking_duration = config.get("lifecycle", {}).get("waking_duration_seconds", 10)
    sleeping_duration = config.get("lifecycle", {}).get("sleeping_duration_seconds", 5)

    log_message("Zahajuji cyklus Bdění a Spánku.")
    orchestrator = Orchestrator(llm=llm)

    while True:
        log_message("STAV: Bdění - Kontrola nových úkolů.")
        memory = AdvancedMemory()
        next_task = await memory.get_next_task()

        if next_task:
            task_id = next_task["chat_id"]
            task_description = next_task["user_input"]
            log_message(f"Nalezen nový úkol: {task_description} (ID: {task_id})")

            # Vytvoření kontextu pro tento úkol
            context = SharedContext(
                session_id=task_id, original_prompt=task_description
            )

            # Spuštění centrálního orchestrátoru
            final_context = await orchestrator.execute_task(context, task_description)

            # Vyhodnocení výsledku a aktualizace stavu
            if "success" in final_context.feedback.lower():
                log_message(f"Úkol {task_id} byl úspěšně dokončen.")
                await memory.update_task_status(task_id, "TASK_COMPLETED")
            else:
                log_message(
                    f"Úkol {task_id} selhal. Finální zpětná vazba: {final_context.feedback}"
                )
                await memory.update_task_status(task_id, "TASK_FAILED")

        else:
            log_message("Žádné nové úkoly ve frontě, odpočívám...")
            await asyncio.sleep(waking_duration)

        memory.close()

        # --- FÁZE SPÁNKU ---
        log_message("STAV: Spánek - Fáze sebereflexe a konsolidace.")
        try:
            memory = AdvancedMemory()
            await memory.add_memory(
                "Waking cycle completed successfully.", "lifecycle_event"
            )
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
            agent=PhilosopherAgent(),
            expected_output="A single, insightful paragraph summarizing the recent past.",
        )
        log_message("Spouštím Filosofa k sebereflexi...")
        try:
            # Spouštění v threadu, aby neblokovalo asyncio loop
            summary = await asyncio.to_thread(reflection_task.execute)
            log_message(f"DREAMING: {summary}")
        except Exception as e:
            log_message(
                f"CHYBA: Došlo k chybě během sebereflexe (PhilosopherAgent): {e}"
            )

        await asyncio.sleep(sleeping_duration)


if __name__ == "__main__":
    asyncio.run(main())
