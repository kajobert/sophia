from crewai import Agent
# Importujeme nové nástroje
from core.custom_tools import LTMemoryTool

# Definice Memory Agenta
memory_agent = Agent(
    role='Cognitive Psychologist',
    goal='Analyze short-term event logs and extract meaningful insights to be stored as long-term memories.',
    backstory="""You are an AI specializing in cognitive science.
    Your job is to review raw event data, identify patterns, key learnings,
    and important facts, and then consolidate them into concise, meaningful memories.""",
    verbose=True,
    allow_delegation=False,
    llm='gemini/gemini-2.5-flash',
    tools=[
        LTMemoryTool()  # Bude potřebovat ukládat do LTM
    ]
)

from crewai import Agent
from core.custom_tools import WebSearchTool, CreateReportTool

developer_agent = Agent(
    role='Autonomous Task Executor',
    goal='Execute multi-step tasks by sequentially using the available tools based on instructions.',
    backstory="""You are a reliable agent that follows instructions perfectly. You use your tools one by one to achieve the final goal.""",
    verbose=True,
    allow_delegation=False,
    llm='gemini/gemini-2.5-flash',
    tools=[
        WebSearchTool(),
        CreateReportTool()
    ]
)
