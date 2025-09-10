from dotenv import load_dotenv
from crewai import Crew, Process

# Načteme API klíč hned na začátku
load_dotenv()

# Importujeme naše agenty a NOVÝ úkol z modulu 'core'
from core.agents import researcher
from core.tasks import code_analysis_task

def main():
    """Hlavní funkce pro sestavení a spuštění Crew."""
    print("🚀 Initializing the Sophia v2 Crew for a code analysis task...")

    # Sestavení posádky s naším agentem a NOVÝM úkolem
    sophia_crew = Crew(
        agents=[researcher],
        tasks=[code_analysis_task],
    process=Process.sequential,
    verbose=True
    )

    print("🏁 Crew assembled. Kicking off the task...")
    result = sophia_crew.kickoff()

    print("\n\n########################")
    print("## ✅ Task Completed!")
    print("## Here is the result:")
    print("########################\n")
    print(result)

if __name__ == "__main__":
    main()
