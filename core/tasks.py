from crewai import Task
from .agents import developer_agent

# Definice úkolu pro aktualizaci dokumentace
documentation_task = Task(
    description="""Read the project's `README.md` file to understand its current content.
    Then, read the `core/custom_tools.py` file to learn about the `CustomFileWriteTool`.
    Finally, update the `README.md` file by adding a new section that describes the `CustomFileWriteTool`,
    including its purpose and how to use it. The new section should be clearly titled 'Custom Tools'.""",
    expected_output="The `README.md` file is updated with a new 'Custom Tools' section describing the `CustomFileWriteTool`.",
    agent=developer_agent,
)
