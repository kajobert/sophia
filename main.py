from dotenv import load_dotenv
from crewai import Crew, Process

# Načtení environmentálních proměnných
load_dotenv()

# Import agenta a nového úkolu
from core.agents import developer_agent
from core.tasks import tool_practice_task

def main():
    """Hlavní funkce pro sestavení a spuštění Crew."""
    print("🚀 Initializing the Sophia v2 Crew for a tool practice task...")

    # Sestavení posádky
    sophia_crew = Crew(
        agents=[developer_agent],
        tasks=[tool_practice_task],
        process=Process.sequential,
        verbose=2
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
