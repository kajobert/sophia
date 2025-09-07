from dotenv import load_dotenv
from crewai import Crew, Process

load_dotenv()

from core.agents import researcher
from core.tasks import web_search_task

def main():
    """Hlavní funkce pro sestavení a spuštění Crew."""
    print("🚀 Initializing the Sophia v2 Crew for a web search task...")

    sophia_crew = Crew(
        agents=[researcher],
        tasks=[web_search_task],
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
