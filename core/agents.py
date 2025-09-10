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
analyst_agent = Agent(
    role="Expert Code Analyst and Reporter",
    goal="Analyze Python source code and generate comprehensive reports based on your findings.",
    backstory="""You are a meticulous software engineer with a deep understanding of code architecture.
    You can read and analyze code to understand its purpose, tools, and parameters,
    and then write your findings into clear, structured text files.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_read_tool, directory_read_tool, file_create_tool],
)
