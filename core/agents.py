import os
from crewai import Agent
from crewai_tools import SerperDevTool
from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                             google_api_key=os.getenv("GEMINI_API_KEY"))

# Inicializace nástroje SerperDevTool pro vyhledávání na webu
search_tool = SerperDevTool()

# Definice našeho agenta, nyní vybaveného spolehlivým vyhledáváním
researcher = Agent(
    role='Senior Research Analyst',
    goal='Uncover cutting-edge developments in AI and data science',
    backstory="""You work at a leading tech think tank.
    Your expertise lies in identifying emerging trends from the web.
    You have a knack for dissecting complex data and presenting
    actionable insights.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool]
)