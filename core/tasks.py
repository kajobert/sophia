
# Nový úkol, který testuje úpravu existujícího souboru
from crewai import Task
from .agents import developer_agent

# Finální testovací úkol, který kombinuje všechny schopnosti
final_integration_task = Task(
    description="""1. Perform a web search to find out who the current CEO of OpenAI is.
    2. Create a new file named 'ceo_report.txt'.
    3. Write the name of the CEO you found into this file.
    4. Read the 'README.md' file.
    5. Append the content of 'README.md' to the 'ceo_report.txt' file.""",
    expected_output="A final confirmation that 'ceo_report.txt' was created and updated with both the CEO's name and the README content.",
    agent=developer_agent
)
final_integration_task = Task(
    description="""1. Perform a web search to find out who the current CEO of OpenAI is.
    2. Create a new file named 'ceo_report.txt'.
    3. Write the name of the CEO you found into this file.
    4. Read the 'README.md' file.
    5. Append the content of 'README.md' to the 'ceo_report.txt' file.""",
    expected_output="A final confirmation that 'ceo_report.txt' was created and updated with both the CEO's name and the README content.",
    agent=developer_agent
)
