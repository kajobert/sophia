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

web_search_task = Task(
    description="""What is the latest version of the 'crewai' Python library available on PyPI?
    Summarize the key new features or changes mentioned for this latest version.
    Your final answer must clearly state the version number you found and then a bulleted list
    of the new features.""",
    expected_output="The latest version number of the crewai library followed by a summary of its new features.",
    agent=researcher
)
