import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from crewai import Crew, Process, Task
from core.agents import developer_agent, planning_agent, archivist_agent
from core.memory_agent import memory_agent
from core.memory_tasks import memory_consolidation_task
from memory.long_term_memory import LongTermMemory
import datetime
import json
from core.token_counter_tool import TokenCounterTool
from memory.episodic_memory import EpisodicMemory


def log_token_usage(input_text: str, output_text: str):
    """Counts tokens for input and output and logs them."""
    token_counter = TokenCounterTool()

    input_text = str(input_text)
    output_text = str(output_text)

    input_tokens = token_counter._run(text=input_text)
    output_tokens = token_counter._run(text=output_text)

    if not isinstance(input_tokens, int):
        input_tokens = 0
    if not isinstance(output_tokens, int):
        output_tokens = 0

    total_tokens = input_tokens + output_tokens

    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"{timestamp}, input_tokens: {input_tokens}, output_tokens: {output_tokens}, total_tokens: {total_tokens}\n"

    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/token_usage.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to token usage log: {e}")


# Global episodic memory instance, initialized in main()
episodic_memory = None


def step_callback(*args, **kwargs):
    """Universal callback for CrewAI agent steps, compatible with various signatures."""
    global episodic_memory
    if not episodic_memory:
        return

    # Try to extract agent_output, agent_name, task from args/kwargs
    agent_output = None
    agent_name = None
    task = None

    # CrewAI sometimes calls with (agent_output), sometimes (agent_output, agent_name, task)
    if len(args) == 1:
        agent_output = args[0]
    elif len(args) == 3:
        agent_output, agent_name, task = args
    # Try kwargs as fallback
    agent_output = agent_output or kwargs.get("agent_output")
    agent_name = agent_name or kwargs.get("agent_name")
    task = task or kwargs.get("task")

    action_str = ""
    input_str = ""
    output_str = ""
    status = ""

    if hasattr(agent_output, "tool") and hasattr(agent_output, "tool_input"):
        action_str = getattr(agent_output, "tool", "")
        input_str = str(getattr(agent_output, "tool_input", ""))
        output_str = getattr(agent_output, "log", "")
        status = "ACTION"
    elif hasattr(agent_output, "return_values"):
        action_str = "Finish"
        input_str = getattr(task, "description", "") if task else ""
        output_str = agent_output.return_values.get("output", "")
        status = "FINISH"
    else:
        action_str = str(agent_output)
        status = "UNKNOWN"

    episodic_memory.add_event(
        agent_name=agent_name or "UnknownAgent",
        action=action_str,
        input_data=input_str,
        output_data=output_str,
        status=status,
    )


def run_memory_consolidation(context_to_memorize):
    """Spustí agenta pro konsolidaci paměti s konkrétním kontextem."""
    memory_crew = Crew(
        tasks=[memory_consolidation_task],
        agents=[memory_agent],
        process=Process.sequential,
    )
    memory_result = memory_crew.kickoff(inputs={"context": context_to_memorize})
    if (
        hasattr(memory_result, "__class__")
        and memory_result.__class__.__name__ == "CrewOutput"
    ):
        memory_result_str = str(memory_result)
    else:
        memory_result_str = str(memory_result)
    print(f"[Proces snění] Rozhodnuto k uložení: {memory_result_str}")
    print("[Proces snění] Konsolidace paměti dokončena.")


def main():
    global episodic_memory
    episodic_memory = EpisodicMemory()

    print(
        "Vítejte! Sophia je připravena. Napište svůj dotaz nebo příkaz. Pro ukončení napište 'exit'."
    )
    episodic_memory.add_event("System", "SessionStart", "", "", "SYSTEM")
    long_term_memory = LongTermMemory()

    while True:
        user_input = input("\nVy: ")
        if user_input.strip().lower() == "exit":
            print("Nashledanou!")
            episodic_memory.add_event("System", "SessionEnd", "", "", "SYSTEM")
            break
        else:
            episodic_memory.add_event("User", "Input", user_input, "", "INPUT")

            # --- Uživatelský kontext ---
            user_name = "Uživatel"
            try:
                with open("uzivatel_jmeno.txt", "r", encoding="utf-8") as f:
                    user_name = f.read().strip() or user_name
            except Exception:
                pass
            user_profile = ""
            profile_path = f"{user_name.lower()}_profile.txt"
            if os.path.exists(profile_path):
                with open(profile_path, "r", encoding="utf-8") as f:
                    user_profile = f.read().strip()

            # --- Klíčové vzpomínky z LTM ---
            try:
                relevant_memories = long_term_memory.fetch_relevant_memories(
                    user_input, num_results=3
                )
            except Exception as e:
                print(
                    f"[LTM] Chyba při načítání paměti: {e}. Pokouším se obnovit databázi..."
                )
                from shutil import rmtree
                import time

                db_path = "memory/chroma_db"
                try:
                    rmtree(db_path)
                except Exception:
                    pass
                time.sleep(0.5)
                long_term_memory = LongTermMemory()
                relevant_memories = long_term_memory.fetch_relevant_memories(
                    user_input, num_results=3
                )

            ltm_context = ""
            if relevant_memories and relevant_memories[0]:
                print("🧠 Nalezeny relevantní vzpomínky, přidávám je do kontextu...")
                context_list = relevant_memories[0]
                ltm_context = "\n".join(context_list)
            elif relevant_memories == [] or (
                relevant_memories and not relevant_memories[0]
            ):
                ltm_context = ""
                print(
                    "ℹ️  Dlouhodobá paměť je prázdná nebo byla resetována. Můžete začít tvořit nové vzpomínky."
                )

            context_parts = []
            context_parts.append(f"Jméno uživatele: {user_name}")
            if user_profile:
                context_parts.append(f"Profil uživatele: {user_profile}")
            if ltm_context:
                context_parts.append(f"Relevantní vzpomínky: {ltm_context}")
            task_context = "\n".join(context_parts)

            # --- Fáze 1: Plánování ---
            print("📝 Fáze 1: Vytvářím plán...")
            planning_task = Task(
                description=(
                    f"Analyzuj požadavek uživatele: '{user_input}'. Vytvoř podrobný plán krok za krokem. "
                    f"Každý krok musí být samostatná, proveditelná akce pro developera.\n"
                    f"Kontext, který máš k dispozici:\n{task_context}\n\n"
                    "Odpověz POUZE ve formátu JSON, který obsahuje seznam s názvem 'plan', kde každá položka je objekt s klíči 'step' a 'description'."
                    'Příklad: {"plan": [{"step": 1, "description": "Popis prvního kroku."}, {"step": 2, "description": "Popis druhého kroku."}]}'
                ),
                expected_output="JSON string se seznamem kroků plánu.",
                agent=planning_agent,
            )

            planning_crew = Crew(
                agents=[planning_agent],
                tasks=[planning_task],
                process=Process.sequential,
                verbose=False,
            )

            plan_result = planning_crew.kickoff()
            episodic_memory.add_event(
                "Sophia", "PlanGenerated", user_input, str(plan_result), "INTERNAL"
            )

            try:
                # Očištění a parsování JSONu
                # LLM může vrátit JSON obalený v markdownu (```json ... ```)
                clean_json_str = (
                    plan_result.strip()
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                plan_data = json.loads(clean_json_str)
                plan_steps = plan_data.get("plan", [])
                if not plan_steps:
                    raise ValueError("Plán neobsahuje žádné kroky.")
                print(f"✅ Plán úspěšně vytvořen s {len(plan_steps)} kroky.")
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"❌ Chyba: Nepodařilo se zpracovat plán. Výstup plánovače nebyl validní JSON. Chyba: {e}"
                )
                print(f"Raw výstup plánovače: {plan_result}")
                result = "Omlouvám se, nepodařilo se mi vytvořit platný plán úkolů. Zkuste prosím přeformulovat svůj požadavek."
                plan_steps = []

            # --- Fáze 2: Vykonávání ---
            if plan_steps:
                print("\n🚀 Fáze 2: Spouštím vykonávání plánu...")
                step_results = []
                for i, step in enumerate(plan_steps):
                    step_description = step.get("description", "Není popsáno.")
                    print(f"   - Krok {i+1}/{len(plan_steps)}: {step_description}")

                    # Předej výstup z předchozího kroku jako kontext
                    previous_results_context = "\n".join(step_results)
                    task_description_with_context = (
                        f"{step_description}\n\n"
                        f"Toto je krok {i+1} z celkových {len(plan_steps)}.\n"
                        f"Kontext z předchozích kroků:\n{previous_results_context}"
                    )

                    execution_task = Task(
                        description=task_description_with_context,
                        expected_output="Výsledek provedeného kroku. Pokud krok generuje soubor, vrať cestu k souboru. Pokud ne, vrať textový popis výsledku.",
                        agent=developer_agent,
                    )

                    execution_crew = Crew(
                        agents=[developer_agent, archivist_agent],
                        tasks=[execution_task],
                        process=Process.sequential,
                        step_callback=step_callback,
                        verbose=False,
                    )

                    step_result = execution_crew.kickoff()
                    episodic_memory.add_event(
                        "Sophia",
                        f"Step_{i+1}_Executed",
                        step_description,
                        str(step_result),
                        "INTERNAL",
                    )
                    print(f"   - Výsledek kroku {i+1}: {step_result}")
                    step_results.append(f"Výsledek kroku {i+1}: {step_result}")

                result = "\n".join(step_results)
            print(f"\nSophia: {result}")
            episodic_memory.add_event(
                "Sophia", "FinalAnswer", user_input, str(result), "OUTPUT"
            )
            log_token_usage(user_input, result)
            run_memory_consolidation(str(result))

            # Break the loop if in mock testing mode to prevent EOFError
            if os.getenv("USE_MOCK_LLM") == "true":
                print("\n--- MOCK TEST: Breaking loop after one run. ---")
                break


if __name__ == "__main__":
    main()
