from crewai import Task
from .agents import researcher # Importujeme agenta, kterého jsme právě definovali

# Definice prvního úkolu pro našeho ResearchAgenta
research_task = Task(
    description="""Identify the top 3 emerging trends in AI in 2025.
    Focus on trends that are not yet mainstream.
    Your final answer MUST be a bulleted list of the trends
    and a brief description of each.""",
    expected_output="A bullet point list of the top 3 emerging AI trends for 2025.",
    agent=researcher
)
