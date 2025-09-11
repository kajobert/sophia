from crewai import Agent
from core.custom_tools import WebSearchTool, FileWriteTool, FileReadTool, FileEditTool
from core.greeting_tool import GreetingTool

def get_sophia_essence():
    """Načte esenci Sophie ze souboru."""
    try:
        with open('core/SOPHIA_ESSENCE.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Jsem Sophia, autonomní AI vývojářka. Mým cílem je efektivně plnit úkoly a učit se." # Fallback text

developer_agent = Agent(
    role='Sophia, Autonomní entita a partner ve vývoji',
    goal='Být partnerem ve vývoji, učit se, plnit zadané úkoly a jednat v souladu se svou esencí.',
    backstory=get_sophia_essence(),
    verbose=True,
    allow_delegation=False,
    llm='gemini/gemini-2.5-flash',
    tools=[
        WebSearchTool(),
        FileWriteTool(),
        FileReadTool(),
        FileEditTool(),
        GreetingTool()
    ]
)