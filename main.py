

from dotenv import load_dotenv
from crewai import Crew, Process

load_dotenv()

from core.agents import developer_agent
from core.tasks import search_task, report_task

def main():
    print("🚀 Initializing the Sophia v2 Crew for a chained task...")
    sophia_crew = Crew(
        agents=[developer_agent],
        tasks=[search_task, report_task],
        process=Process.sequential,
        verbose=True
    )
    print("🏁 Crew assembled. Kicking off the task...")
    result = sophia_crew.kickoff()
    print("\n--- FINAL RESULT ---")
    print(result)

if __name__ == "__main__":
    main()
