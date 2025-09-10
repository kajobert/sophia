
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
