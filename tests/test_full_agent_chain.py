import pytest
from crewai import Crew, Task
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from core.context import SharedContext

def test_planner_with_shared_context():
    """
    Tests the PlannerAgent's integration with the SharedContext.
    """
    # 1. Vytvoření instance agenta a kontextu
    planner = PlannerAgent()
    prompt = "Vytvoř plán pro jednoduchou funkci 'add(a, b)', která sčítá dvě čísla."
    context = SharedContext(session_id="test_session", original_prompt=prompt)

    # 2. Spuštění úkolu
    updated_context = planner.run_task(context)

    # 3. Ověření výsledku
    assert isinstance(updated_context, SharedContext)
    assert 'plan' in updated_context.payload
    # Mock LLM should return a specific plan
    assert "Definuj funkci `add(a, b)`" in updated_context.payload['plan']
    print(f"\n--- Planner Result ---\n{updated_context.payload['plan']}\n------------------------")


def test_linear_agent_collaboration_with_context():
    """
    Testuje E2E spolupráci agentů s využitím SharedContext.
    Planner nejprve vytvoří plán do kontextu, Engineer ho pak použije.
    """
    # 1. Fáze Plánování
    planner = PlannerAgent()
    prompt = "Vytvoř plán pro jednoduchou funkci 'add(a, b)', která sčítá dvě čísla."
    context = SharedContext(session_id="test_session_e2e", original_prompt=prompt)

    context_with_plan = planner.run_task(context)

    assert "Definuj funkci `add(a, b)`" in context_with_plan.payload['plan']

    # 2. Fáze Inženýringu
    engineer_agent = EngineerAgent().get_agent()

    # Inženýrský úkol nyní používá plán z kontextu.
    coding_task = Task(
        description=f"Na základě tohoto plánu vytvoř kód v Pythonu: {context_with_plan.payload['plan']}",
        agent=engineer_agent,
        expected_output="Funkční a okomentovaný kód v Pythonu."
    )

    # Spustíme pouze inženýrský úkol
    crew = Crew(
        agents=[engineer_agent],
        tasks=[coding_task],
        verbose=True
    )

    result = crew.kickoff()

    # 3. Ověření konečného výsledku
    print(f"\n--- Final Crew Result ---\n{result}\n------------------------")
    assert result is not None
    assert "def add(a, b):" in result.raw
    assert "return a + b" in result.raw
    assert "plán" not in result.raw.lower()
