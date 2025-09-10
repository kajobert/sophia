from crewai import Task
from .agents import developer_agent

# Nový úkol, který testuje sekvenční použití nástrojů
directory_analysis_task = Task(
    description="""1. First, list all files and directories within the 'core/' directory.
    2. After you have the list, read the content of the 'core/tasks.py' file specifically.
    3. Finally, analyze the file's content and describe the purpose of the task defined inside it.
    Your final answer should be a short summary of the task's purpose.""",
    expected_output="A concise summary explaining the goal of the task found in 'core/tasks.py'.",
    agent=developer_agent
)
