
import os
from dotenv import load_dotenv
from crewai import Crew, Process, Task
from core.agents import developer_agent
from core.memory_agent import memory_agent
from core.memory_tasks import memory_consolidation_task
from memory.long_term_memory import LongTermMemory
def run_memory_consolidation(context_to_memorize):
    """Spustí agenta pro konsolidaci paměti s konkrétním kontextem."""
    memory_crew = Crew(
        tasks=[memory_consolidation_task],
        agents=[memory_agent],
        process=Process.sequential
    )
    # Spustíme kickoff s kontextem, který se dosadí do description úkolu
    memory_result = memory_crew.kickoff(inputs={'context': context_to_memorize})
    # Pokud je výstup CrewOutput, použijeme jeho textovou reprezentaci
    if hasattr(memory_result, '__class__') and memory_result.__class__.__name__ == 'CrewOutput':
        memory_result_str = str(memory_result)
    else:
        memory_result_str = str(memory_result)
    print(f"[Proces snění] Rozhodnuto k uložení: {memory_result_str}")
    print("[Proces snění] Konsolidace paměti dokončena.")
from memory.short_term_memory import ShortTermMemory
from crewai.agents import AgentAction, AgentFinish

load_dotenv()

# Global memory instance
short_term_memory = ShortTermMemory()

def step_callback(agent_action):
    if isinstance(agent_action, AgentAction):
        thought = getattr(agent_action, 'thought', None)
        tool = getattr(agent_action, 'tool', None)
        if thought or tool:
            short_term_memory.add_event(f"AgentAction: thought={thought}, tool={tool}")
    elif isinstance(agent_action, AgentFinish):
        output = getattr(agent_action, 'output', None)
        if output:
            short_term_memory.add_event(f"AgentFinish: output={output}")

def main():
    print("Vítejte! Sophia je připravena. Napište svůj dotaz nebo příkaz. Pro ukončení napište 'exit'.")
    short_term_memory.add_event("Session started.")
    long_term_memory = LongTermMemory()
    while True:
        user_input = input("\nVy: ")
        if user_input.strip().lower() == 'exit':
            print("Nashledanou!")
            short_term_memory.add_event("Session ended.")
            break
        else:
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
            # Robustní fetch relevantních vzpomínek s automatickou obnovou ChromaDB
            try:
                relevant_memories = long_term_memory.fetch_relevant_memories(user_input, num_results=3)
            except Exception as e:
                print(f"[LTM] Chyba při načítání paměti: {e}. Pokouším se obnovit databázi...")
                from shutil import rmtree
                import time
                db_path = "memory/chroma_db"
                try:
                    rmtree(db_path)
                except Exception:
                    pass
                time.sleep(0.5)
                long_term_memory = LongTermMemory()
                relevant_memories = long_term_memory.fetch_relevant_memories(user_input, num_results=3)
            ltm_context = ""
            if relevant_memories and relevant_memories[0]:
                print("🧠 Nalezeny relevantní vzpomínky, přidávám je do kontextu...")
                context_list = relevant_memories[0]
                ltm_context = "\n".join(context_list)
            elif relevant_memories == [] or (relevant_memories and not relevant_memories[0]):
                ltm_context = ""
                print("ℹ️  Dlouhodobá paměť je prázdná nebo byla resetována. Můžete začít tvořit nové vzpomínky.")
            # --- Detekce paměťového záměru ---
            memory_keywords = [
                "zapamatuj", "ulož do paměti", "vzpomínka", "remember", "memory", "pamatuj si", "ulož si", "save to memory", "store in memory"
            ]
            lower_input = user_input.lower()
            if any(kw in lower_input for kw in memory_keywords):
                from core.ltm_write_tool import LtmWriteTool
                ltm_check = LongTermMemory()
                if getattr(ltm_check, 'collection', None) is None:
                    result = "Dlouhodobá paměť není dostupná. Informace nebyla uložena. Prosím, kontaktujte správce systému."
                    print(f"\nSophia (LTM): {result}")
                    short_term_memory.add_event(f"User: {user_input}")
                    short_term_memory.add_event(f"Sophia: {result}")
                    return  # Zamezí dalšímu zpracování paměťového promptu CrewAI
                else:
                    ltm_tool = LtmWriteTool()
                    result = ltm_tool._run(user_input)
                    print(f"\nSophia (LTM): {result}")
                    short_term_memory.add_event(f"User: {user_input}")
                    short_term_memory.add_event(f"Sophia: {result}")
                    run_memory_consolidation(str(result))
                    return  # Zamezí dalšímu zpracování paměťového promptu CrewAI
            context_parts = []
            context_parts.append(f"Jméno uživatele: {user_name}")
            if user_profile:
                context_parts.append(f"Profil uživatele: {user_profile}")
            if ltm_context:
                context_parts.append(f"Relevantní vzpomínky: {ltm_context}")
            task_context = "\n".join(context_parts)
            # Dynamicky vytvoření Task s rozšířeným kontextem
            task = Task(
                description=f"Na základě následujícího kontextu: '{task_context}'\n--- Zpracuj tento požadavek: '{user_input}'",
                expected_output="Stručná a přesná odpověď nebo potvrzení o provedení akce.",
                agent=developer_agent
            )
            crew = Crew(
                tasks=[task],
                agents=[developer_agent],
                process=Process.sequential,
                step_callback=step_callback
            )
            result = crew.kickoff()
            print(f"\nSophia: {result}")
            short_term_memory.add_event(f"User: {user_input}")
            short_term_memory.add_event(f"Sophia: {result}")
            run_memory_consolidation(str(result))

if __name__ == "__main__":
    main()
