
import os
from dotenv import load_dotenv
from crewai import Crew, Process, Task
from core.agents import developer_agent
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
    while True:
        user_input = input("\nVy: ")
        if user_input.strip().lower() == 'exit':
            print("Nashledanou!")
            short_term_memory.add_event("Session ended.")
            break
        else:
            # Dynamically create a Task for the agent
            task = Task(
                description=f"Zpracuj následující požadavek: '{user_input}'. Pokud je to příkaz, použij dostupné nástroje.",
                expected_output="Stručně odpověz nebo proveď požadovanou akci a popiš výsledek.",
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

if __name__ == "__main__":
    main()
