
import os
from dotenv import load_dotenv
from crewai import Crew, Process, Task
from core.agents import developer_agent
from core.memory_agent import memory_agent
from core.memory_tasks import memory_consolidation_task
from memory.long_term_memory import LongTermMemory
def run_memory_consolidation():
    crew = Crew(
        tasks=[memory_consolidation_task],
        agents=[memory_agent],
        process=Process.sequential
    )
    crew.kickoff()
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
            # Aktivní vybavení relevantních vzpomínek z LTM
            relevant_memories = long_term_memory.fetch_relevant_memories(user_input, num_results=3)
            task_context = ""
            if relevant_memories:
                print("🧠 Nalezeny relevantní vzpomínky, přidávám je do kontextu...")
                context_list = relevant_memories[0] if relevant_memories else []
                task_context = "\n".join(context_list)
            # Dynamicky vytvoření Task s kontextem z LTM
            task = Task(
                description=f"Na základě následujícího kontextu z mé dlouhodobé paměti: '{task_context}'\n--- Zpracuj tento požadavek: '{user_input}'",
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
            run_memory_consolidation()

if __name__ == "__main__":
    main()
