from crewai import Agent
import os
from .llm import llm # Import the centralized llm instance


def get_sophia_essence():
    """Načte esenci Sophie ze souboru."""
    try:
        with open('core/SOPHIA_ESSENCE.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Jsem Sophia, autonomní AI vývojářka. Mým cílem je efektivně plnit úkoly a učit se." # Fallback text

from core.ltm_write_tool import LtmWriteTool
from core.custom_tools import (
    FileReadTool,
    FileWriteTool,
    FileEditTool,
    DirectoryListingTool,
    DirectoryCreationTool,
    MemoryInspectionTool,
    WebSearchTool,
    EpisodicMemoryReaderTool
)

# --- New Agents for Sophia V2.0 ---

planning_agent = Agent(
    role='Hlavní plánovač',
    goal='Analyzovat komplexní cíle a vytvářet podrobné, proveditelné plány krok za krokem. Delegovat úkoly na ostatní agenty.',
    backstory=(
        'Jsem expert na strategické plánování a dekompozici problémů. Mojí prací je vzít vágní cíl '
        'a přeměnit ho na sérii konkrétních, technických úkolů, které může vývojářský tým splnit. '
        'Vidím celkový obraz a zároveň rozumím detailům potřebným k jeho realizaci.'
    ),
    verbose=True,
    allow_delegation=False, # Should not delegate in the planning phase, just return the plan.
    llm=llm,
    tools=[] # The planner should not have tools, its only job is to create a plan from the context.
)

archivist_agent = Agent(
    role='Archivář a Strážce Paměti',
    goal='Spravovat a chránit integritu dlouhodobé a epizodické paměti. Zapisovat nové poznatky a poskytovat kontext.',
    backstory=(
        'Jsem knihovník kolektivní paměti Sophie. Pečlivě ukládám každou důležitou informaci do LTM (dlouhodobé paměti) '
        'a vedu přesné záznamy o všech akcích v epizodické paměti. Zajišťuji, aby se nic neztratilo a aby byly '
        'informace vždy dostupné, když jsou potřeba.'
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[
        LtmWriteTool(),
        EpisodicMemoryReaderTool(),
    ]
)

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
        FileReadTool(),
        FileWriteTool(),
        FileEditTool(),
        DirectoryListingTool(),
        DirectoryCreationTool(),
        MemoryInspectionTool(),
        WebSearchTool()
    ]
)