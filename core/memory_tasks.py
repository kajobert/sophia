from crewai import Task
from core.memory_agent import memory_agent

memory_consolidation_task = Task(
    description="Analyzuj poslední události ze short-term memory a ulož klíčové poznatky do long-term memory.",
    expected_output="Klíčové poznatky byly úspěšně uloženy do dlouhodobé paměti.",
    agent=memory_agent
)
