from crewai import Task
# Úkol pro konsolidaci paměti
from .agents import memory_agent

# Úkol pro konsolidaci paměti
memory_consolidation_task = Task(
    description="""1. Read the entire content of the short-term memory log located at 'logs/episodic_memory.log'.
    2. Analyze the log and identify 3 to 5 key events, learnings, or facts from the recent activities. For example, 'The agent learned that the CEO of NVIDIA is Jensen Huang.' or 'A file named ceo_report.txt was created.'
    3. For EACH of these key insights, use the 'Long-Term Memory Storage Tool' to save it as a distinct memory.""",
    expected_output="A confirmation that key insights from the short-term log have been identified and stored in long-term memory.",
    agent=memory_agent
)
from crewai import Task
from .agents import developer_agent

# Úkol č. 1: Pouze vyhledávání informací
search_task = Task(
    description="Perform a web search to find out who the current CEO of NVIDIA is. Focus only on finding the name.",
    expected_output="The full name of the current CEO of NVIDIA.",
    agent=developer_agent
)

# Úkol č. 2: Vytvoření reportu na základě výsledků z předchozího úkolu
report_task = Task(
    description="""Create a new report file named 'ceo_nvidia_report.txt'.
    Write the name of the CEO you found in the previous task into this file.
    The content should be a simple sentence, e.g., 'The current CEO of NVIDIA is [Name]'.""",
    expected_output="A confirmation that the file 'ceo_nvidia_report.txt' was created with the correct sentence.",
    agent=developer_agent,
    context=[search_task]
)

# Nový úkol, který testuje úpravu existujícího souboru


from crewai import Task
from .agents import developer_agent

integration_task = Task(
    description="""Execute the task in three steps using your tools:
    1. First, use the 'Web Search Tool' to find the required information.
    2. Then, use the 'Create Report Tool' to save the result from step 1 into a file. The content you pass to this tool should be the direct result from the search.
    3. Finally, use the 'Append README Tool' to add the project's README to the report.""",
    expected_output="A final confirmation that all three steps were completed successfully.",
    agent=developer_agent
)
