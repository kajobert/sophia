from crewai import Task
from .agents import developer_agent

# Úkol č. 1: Pouze vyhledávání informací
search_task = Task(
	description="Perform a web search to find out who the current CEO of NVIDIA is. Focus only on finding the name.",
	expected_output="The full name of the current CEO of NVIDIA.",
	agent=developer_agent
)

# Úkol č. 2: Vytvoření reportu na základě výsledků z PŘEDCHOZÍHO úkolu
report_task = Task(
	description="""Create a new report file named 'ceo_nvidia_report.txt'.
	Write the name of the CEO you found in the previous task into this file.
	The content should be a simple sentence, e.g., 'The current CEO of NVIDIA is [Name]'.""",
	expected_output="A confirmation that the file 'ceo_nvidia_report.txt' was created with the correct sentence.",
	agent=developer_agent,
	# Tento klíčový parametr říká, že tento úkol potřebuje výstup z předchozích úkolů
	context=[search_task]
)
"""
This file is intentionally left empty.
Tasks will be created dynamically in main.py based on user input.
"""
