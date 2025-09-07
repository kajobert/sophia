from dotenv import load_dotenv
from crewai import Crew, Process

# Načteme API klíč hned na začátku
load_dotenv()

# Importujeme naše agenty a úkoly z modulu 'core'
from core.agents import researcher
from core.tasks import research_task

def main():
    """Hlavní funkce pro sestavení a spuštění Crew."""
    print("🚀 Initializing the Sophia v2 Crew...")

    # Sestavení posádky s naším agentem a úkolem
    sophia_crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        process=Process.sequential, # Úkoly poběží jeden po druhém
        verbose=2 # Vypíše kompletní log myšlenkových pochodů agenta
    )

    print("🏁 Crew assembled. Kicking off the task...")
    # Spuštění mise!
    result = sophia_crew.kickoff()

    print("\n\n########################")
    print("## ✅ Task Completed!")
    print("## Here is the result:")
    print("########################\n")
    print(result)

if __name__ == "__main__":
    main()
