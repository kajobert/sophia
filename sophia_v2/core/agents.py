from crewai import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from crewai_tools import DuckDuckGoSearchRunTool

# Inicializujeme LLM, který budou agenti používat
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                             google_api_key=os.getenv("GEMINI_API_KEY"))

# Inicializace nástroje
search_tool = DuckDuckGoSearchRunTool()

# Definice našeho prvního agenta: ResearchAgent
researcher = Agent(
    role='Senior Research Analyst',
    goal='Uncover cutting-edge developments in AI and data science',
    backstory="""You work at a leading tech think tank.
    Your expertise lies in identifying emerging trends.
    You have a knack for dissecting complex data and presenting
    actionable insights.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool]
)
