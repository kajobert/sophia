import pytest
from crewai import Crew, Task
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent

def test_linear_agent_collaboration():
    """
    Testuje E2E spolupráci agentů v jednoduchém lineárním řetězci.
    Díky conftest.py se tento test spustí s mockovaným LLM, který simuluje
    odpovědi pro plánování a kódování.
    """
    # 1. Vytvoření instancí agentů
    planner_agent = PlannerAgent().get_agent()
    engineer_agent = EngineerAgent().get_agent()

    # 2. Vytvoření úkolů pro agenty
    planning_task = Task(
        description="Vytvoř plán pro jednoduchou funkci 'add(a, b)', která sčítá dvě čísla.",
        agent=planner_agent,
        expected_output="Podrobný plán krok za krokem."
    )

    # Inženýrský úkol závisí na výsledku plánovacího úkolu.
    # Jeho výstup použije jako kontext.
    coding_task = Task(
        description="Na základě plánu vytvoř kód v Pythonu.",
        agent=engineer_agent,
        context=[planning_task],
        expected_output="Funkční a okomentovaný kód v Pythonu."
    )

    # 3. Sestavení a spuštění Crew
    crew = Crew(
        agents=[planner_agent, engineer_agent],
        tasks=[planning_task, coding_task],
        verbose=True # Verbose pro logování průběhu
    )

    result = crew.kickoff()

    # 4. Ověření výsledku
    # `crew.kickoff()` vrací výsledek posledního úkolu v řetězci.
    # Náš mock by měl pro inženýrský úkol vrátit kód.
    print(f"\n--- Final Crew Result ---\n{result}\n------------------------")

    assert result is not None
    # The result object has a 'raw' attribute containing the string output
    assert "def add(a, b):" in result.raw
    assert "return a + b" in result.raw
    # Můžeme také ověřit, že se nevrací plán
    assert "plán" not in result.raw.lower()
