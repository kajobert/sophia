import os
from crewai import Agent
from crewai_tools import SerperDevTool, FileReadTool, DirectoryReadTool
from .custom_tools import CustomFileWriteTool
from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest", google_api_key=os.getenv("GEMINI_API_KEY")
)

# Inicializace nástrojů
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
directory_read_tool = DirectoryReadTool()
file_create_tool = CustomFileWriteTool()

# Definice agenta s novou rolí a nástrojem pro zápis
developer_agent = Agent(
    role="Proactive Software Developer",
    goal="Autonomously improve the project by adding new features, fixing bugs, and enhancing documentation.",
    backstory="""You are a skilled software developer, capable of not just analyzing code but also actively improving it.
    You can identify areas for enhancement, write new code, and update documentation to keep it current.
    You are a key contributor to the project's evolution.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_read_tool, directory_read_tool, file_create_tool],
)
