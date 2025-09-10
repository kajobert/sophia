from crewai import Task
from .agents import analyst_agent

# Nový úkol, který vyžaduje čtení a následný zápis do souboru
reporting_task = Task(
    description="""1. Read the content of the 'core/agents.py' file.
    2. Identify the 'role' and 'goal' of the agent defined in that file.
    3. Create a new file named 'analysis_report.txt'.
    4. Write a report into this new file containing the identified role and goal.
    The report should be a simple text: 'Agent Role: [role]\\nAgent Goal: [goal]'.""",
    expected_output="Confirmation that the 'analysis_report.txt' file was created, with a brief summary of its content.",
    agent=analyst_agent,
)
