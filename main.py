import os
from dotenv import load_dotenv
from crewai import Crew, Process, Task
from core.agents import developer_agent, planning_agent, archivist_agent, llm
from core.memory_agent import memory_agent
from core.memory_tasks import memory_consolidation_task
from memory.long_term_memory import LongTermMemory
import datetime
from core.token_counter_tool import TokenCounterTool
from memory.episodic_memory import EpisodicMemory


load_dotenv()

def log_token_usage(input_text: str, output_text: str):
    """Counts tokens for input and output and logs them."""
    token_counter = TokenCounterTool()

    input_text = str(input_text)
    output_text = str(output_text)

    input_tokens = token_counter._run(text=input_text)
    output_tokens = token_counter._run(text=output_text)

    if not isinstance(input_tokens, int): input_tokens = 0
    if not isinstance(output_tokens, int): output_tokens = 0

    total_tokens = input_tokens + output_tokens

    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"{timestamp}, input_tokens: {input_tokens}, output_tokens: {output_tokens}, total_tokens: {total_tokens}\n"

    try:
        os.makedirs('logs', exist_ok=True)
        with open('logs/token_usage.log', 'a', encoding='utf-8') as f:
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
    agent_output = agent_output or kwargs.get('agent_output')
    agent_name = agent_name or kwargs.get('agent_name')
    task = task or kwargs.get('task')

    action_str = ""
    input_str = ""
    output_str = ""
    status = ""

    if hasattr(agent_output, 'tool') and hasattr(agent_output, 'tool_input'):
        action_str = getattr(agent_output, 'tool', '')
        input_str = str(getattr(agent_output, 'tool_input', ''))
        output_str = getattr(agent_output, 'log', '')
        status = "ACTION"
    elif hasattr(agent_output, 'return_values'):
        action_str = "Finish"
        input_str = getattr(task, 'description', '') if task else ''
        output_str = agent_output.return_values.get('output', '')
        status = "FINISH"
    else:
        action_str = str(agent_output)
        status = "UNKNOWN"

    episodic_memory.add_event(
        agent_name=agent_name or "UnknownAgent",
        action=action_str,
        input_data=input_str,
        output_data=output_str,
        status=status
    )

def run_memory_consolidation(context_to_memorize):
    """Spustí agenta pro konsolidaci paměti s konkrétním kontextem."""
    memory_crew = Crew(
        tasks=[memory_consolidation_task],
        agents=[memory_agent],
        process=Process.sequential
    )
    memory_result = memory_crew.kickoff(inputs={'context': context_to_memorize})
    if hasattr(memory_result, '__class__') and memory_result.__class__.__name__ == 'CrewOutput':
        memory_result_str = str(memory_result)
    else:
        memory_result_str = str(memory_result)
    print(f"[Proces snění] Rozhodnuto k uložení: {memory_result_str}")
    print("[Proces snění] Konsolidace paměti dokončena.")

def main():
    global episodic_memory
    episodic_memory = EpisodicMemory()

    print("Vítejte! Sophia je připravena. Napište svůj dotaz nebo příkaz. Pro ukončení napište 'exit'.")
    episodic_memory.add_event("System", "SessionStart", "", "", "SYSTEM")
    long_term_memory = LongTermMemory()

    while True:
        user_input = input("\nVy: ")
        if user_input.strip().lower() == 'exit':
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


            context_parts = []
            context_parts.append(f"Jméno uživatele: {user_name}")
            if user_profile:
                context_parts.append(f"Profil uživatele: {user_profile}")
            if ltm_context:
                context_parts.append(f"Relevantní vzpomínky: {ltm_context}")
            task_context = "\n".join(context_parts)

            # Create the planning task for the hierarchical crew
            planning_task = Task(
                description=f"Vytvoř podrobný, krok-za-krokem plán pro splnění tohoto požadavku od uživatele: '{user_input}'.\n"
                            f"Kontext, který máš k dispozici:\n{task_context}\n\n"
                            "Deleguj jednotlivé kroky plánu na příslušné agenty (developer_agent, archivist_agent).",
                expected_output="Kompletní, dobře strukturovaný a delegovaný plán provedení.",
                agent=planning_agent
            )

            # Assemble the new hierarchical crew
            crew = Crew(
                agents=[planning_agent, developer_agent, archivist_agent],
                tasks=[planning_task],
                process=Process.hierarchical,
                manager_llm=llm,  # Explicitly set the manager LLM
                step_callback=step_callback
            )

            result = crew.kickoff()
            print(f"\nSophia: {result}")
            episodic_memory.add_event("Sophia", "FinalAnswer", user_input, str(result), "OUTPUT")
            log_token_usage(user_input, result)
            run_memory_consolidation(str(result))

if __name__ == "__main__":
    main()
