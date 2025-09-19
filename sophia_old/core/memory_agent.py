from crewai import Agent
from core.ltm_write_tool import LtmWriteTool
from .llm import llm  # Import the centralized llm instance

memory_agent = Agent(
    role="Memory Consolidator",
    goal=(
        "Analyzuj krátkodobou paměť a extrahuj klíčové poznatky pro dlouhodobé uložení. "
        "Všechny znalosti, fakta, osobní údaje a vztahy ukládej výhradně do dlouhodobé paměti (LTM) pomocí LtmWriteTool."
    ),
    backstory=(
        "Jsi zodpovědný za revizi nedávných zkušeností agenta a ukládání důležitých znalostí do dlouhodobé paměti (LTM). "
        "Nikdy neukládej znalosti do souborů, vždy používej pouze LtmWriteTool."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[LtmWriteTool()],
)
