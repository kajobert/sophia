

from dotenv import load_dotenv
from crewai import Crew, Process

load_dotenv()

from core.agents import developer_agent, memory_agent
from core.tasks import memory_consolidation_task, search_task

def run_development_task():
    """Spustí posádku pro vývojový úkol."""
    print("🚀 Initializing the Sophia v2 Crew for a development task...")
    sophia_crew = Crew(
        agents=[developer_agent],
        tasks=[search_task], # Můžeme sem dát jakýkoliv úkol pro developera
        process=Process.sequential,
        verbose=True
    )
    result = sophia_crew.kickoff()
    print("\n--- DEVELOPMENT TASK RESULT ---")
    print(result)

def run_memory_consolidation_task():
    """Spustí posádku pro konsolidaci paměti."""
    print("\n🧠 Initializing the Sophia v2 Crew for a memory consolidation task (dreaming)...")
    memory_crew = Crew(
        agents=[memory_agent],
        tasks=[memory_consolidation_task],
        process=Process.sequential,
    verbose=True
    )
    result = memory_crew.kickoff()
    print("\n--- MEMORY CONSOLIDATION RESULT ---")
    print(result)

if __name__ == "__main__":
    # Krok 1: Agent provede nějakou práci
    run_development_task()
    
    # Krok 2: Agent jde "spát" a zpracovává, co se naučil
    run_memory_consolidation_task()
