from crewai import Agent
from core.custom_tools import DecisionTool
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Initialize LLM
gemini_api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key)

# Add a generic Respond Tool to handle non-tool actions (like greetings)


def get_sophia_essence():
    """Načte esenci Sophie ze souboru."""
    try:
        with open('core/SOPHIA_ESSENCE.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Jsem Sophia, autonomní AI vývojářka. Mým cílem je efektivně plnit úkoly a učit se." # Fallback text

from core.ltm_write_tool import LtmWriteTool
from core.custom_tools import DecisionTool
developer_agent = Agent(
    role='Sophia, Autonomní entita a partner ve vývoji',
    goal=(
        'Být partnerem ve vývoji, učit se, plnit zadané úkoly a jednat v souladu se svou esencí. '
        'Všechny znalosti, fakta, osobní údaje a vztahy ukládej výhradně do dlouhodobé paměti (LTM) pomocí LtmWriteTool. '
        'Soubory používej pouze pro pracovní poznámky, logy nebo dočasná data, nikdy pro znalosti.'
    ),
    backstory=(
        get_sophia_essence() + '\n\n'
        'Instrukce: Pokud máš uložit jakýkoli fakt, osobní údaj, vztah, jméno, preferenci nebo znalost, vždy použij LtmWriteTool. '
        'FileWriteTool a FileEditTool používej pouze pro pracovní poznámky, logy nebo dočasná data, nikdy pro znalosti. '
        'Pokud si nejsi jistá, vždy preferuj zápis do LTM. Při dotazu na znalost vždy čti pouze z LTM.'
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[
        LtmWriteTool(),
        DecisionTool(),
    ]
)