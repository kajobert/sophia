from crewai import Agent
from core.ltm_write_tool import LtmWriteTool
from langchain_google_genai import ChatGoogleGenerativeAI
import os

gemini_api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key)

memory_agent = Agent(
    role='Memory Consolidator',
    goal=(
        'Analyzuj krátkodobou paměť a extrahuj klíčové poznatky pro dlouhodobé uložení. '
        'Všechny znalosti, fakta, osobní údaje a vztahy ukládej výhradně do dlouhodobé paměti (LTM) pomocí LtmWriteTool.'
    ),
    backstory=(
        'Jsi zodpovědný za revizi nedávných zkušeností agenta a ukládání důležitých znalostí do dlouhodobé paměti (LTM). '
        'Nikdy neukládej znalosti do souborů, vždy používej pouze LtmWriteTool.'
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[LtmWriteTool]
)