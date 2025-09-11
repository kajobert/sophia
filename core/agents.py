from crewai import Agent
from core.custom_tools import WebSearchTool, FileWriteTool, FileReadTool, FileEditTool

developer_agent = Agent(
    role='Autonomous Software Developer',
    goal='Execute tasks by correctly using the Web Search, File Write, File Read, and File Edit tools.',
    backstory="You are a reliable agent that can read, write, and edit files, and search the web as instructed.",
    verbose=True,
    allow_delegation=False,
    llm='gemini/gemini-2.5-flash',
    tools=[
        WebSearchTool(),
        FileWriteTool(),
        FileReadTool(),
        FileEditTool()
    ]
)
