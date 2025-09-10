from crewai import Task
from .agents import developer_agent

# Jednoduchý úkol pro otestování jednoho nástroje
tool_practice_task = Task(
    description="""List all files and directories that are inside the 'core/' directory.
    Do not read any of the files, just list them.""",
    expected_output="A list of all filenames and directory names found in the 'core/' directory.",
    agent=developer_agent
)
