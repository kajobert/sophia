import os
from crewai import Agent

# Importujeme naše vlastní nástroje
from core.custom_tools import CustomFileWriteTool, CustomDirectoryListTool
from crewai_tools import SerperDevTool, FileReadTool

from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                             google_api_key=os.getenv("GEMINI_API_KEY"))

# Inicializace nástrojů - nyní používáme náš vlastní
search_tool = SerperDevTool()
file_read_tool = FileReadTool()

directory_list_tool = CustomDirectoryListTool() # <-- ZMĚNA ZDE
file_write_tool = CustomFileWriteTool()

# Definice agenta
developer_agent = Agent(
    role='Autonomous Software Developer',
    goal='Read, analyze, and improve the project codebase and documentation.',
    backstory="""You are a skilled software developer agent.
    Your purpose is to autonomously maintain and enhance the project you are a part of.
    You can read existing files, understand their purpose, and write new content or code to improve them.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    # Nahrazení nástroje v seznamu
    tools=[search_tool, file_read_tool, directory_list_tool, file_write_tool] # <-- ZMĚNA ZDE

)
