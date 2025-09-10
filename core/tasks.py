from crewai import Task
from .agents import researcher

# Nový úkol, který vyžaduje čtení lokálního souboru
code_analysis_task = Task(
    description="""Read the content of the 'core/agents.py' file.
    Based on the code, identify the 'role', 'goal', and the list of 'tools'
    assigned to the agent defined in that file.
    Your final answer MUST be a clear, bulleted list of these three pieces of information.""",
    expected_output="A bullet point list containing the role, goal, and tools of the agent.",
    agent=researcher
)
