import os
from crewai import Agent
from core.custom_tools import (
    CustomFileWriteTool, 
    CustomDirectoryListTool, 
    CustomFilePatchTool,
    SerperDevTool,
    FileReadTool
)

# Definice agenta
developer_agent = Agent(
    role='Autonomous Software Developer',
    goal='Read, analyze, modify, and improve the project codebase and documentation.',
    backstory="""You are a skilled software developer agent. You autonomously maintain and enhance the project.""",
    verbose=True,
    allow_delegation=False,
    # Přímá definice LLM pro crewai/litellm.
    # CrewAI si automaticky načte GEMINI_API_KEY z .env souboru.
    llm='gemini/gemini-2.5-flash',
    tools=[
        SerperDevTool(),
        FileReadTool(),
        CustomDirectoryListTool(),
        CustomFileWriteTool(),
        CustomFilePatchTool()
    ]
)
