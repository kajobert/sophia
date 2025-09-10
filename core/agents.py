import os
from crewai import Agent
from crewai_tools import SerperDevTool, FileReadTool, DirectoryReadTool
from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                             google_api_key=os.getenv("GEMINI_API_KEY"))

# Inicializace nástrojů
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
directory_read_tool = DirectoryReadTool()

# Definice agenta, nyní s rozšířenými schopnostmi
researcher = Agent(
    role='Senior Source Code Analyst',
    goal='Analyze source code and project structures to understand their functionality',
    backstory="""You are an expert software developer.
    Your expertise lies in analyzing complex codebases and project layouts.
    You have a knack for reading code and explaining its purpose clearly.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_read_tool, directory_read_tool]
)