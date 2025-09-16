import pytest
from crewai import Crew, Task
from agents.planner_agent import PlannerAgent
from agents.engineer_agent import EngineerAgent
from agents.tester_agent import TesterAgent
from core.context import SharedContext
from core.llm_config import get_llm

def test_planner_with_shared_context():
    """
    Tests the PlannerAgent's integration with the SharedContext.
    """
    # 1. Vytvoření instance agenta a kontextu
    llm = get_llm()
    planner = PlannerAgent(llm=llm)
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


def test_linear_agent_collaboration():
    """
    Tests the E2E collaboration of agents using SharedContext.
    The Planner first creates a plan in the context, which the Engineer then uses.
    """
    llm = get_llm()
    # 1. Planning Phase
    planner = PlannerAgent(llm=llm)
    prompt = "Vytvoř plán pro jednoduchou funkci 'add(a, b)', která sčítá dvě čísla."
    context = SharedContext(session_id="test_session_e2e", original_prompt=prompt)

    context_with_plan = planner.run_task(context)

    assert 'plan' in context_with_plan.payload
    assert "Definuj funkci `add(a, b)`" in context_with_plan.payload['plan']

    # 2. Engineering Phase
    engineer = EngineerAgent(llm=llm)
    context_with_code = engineer.run_task(context_with_plan)

    assert 'code' in context_with_code.payload
    assert "def add(a, b):" in context_with_code.payload['code']

    # 3. Testing Phase
    tester = TesterAgent(llm=llm)
    final_context = tester.run_task(context_with_code)

    # 4. Verification of the Final Result
    assert isinstance(final_context, SharedContext)
    assert 'plan' in final_context.payload
    assert 'code' in final_context.payload
    assert 'test_results' in final_context.payload

    plan = final_context.payload['plan']
    code = final_context.payload['code']
    test_results = final_context.payload['test_results']

    print(f"\n--- Final Context Plan ---\n{plan}\n--------------------------")
    print(f"\n--- Final Context Code ---\n{code}\n--------------------------")
    print(f"\n--- Final Context Test Results ---\n{test_results}\n---------------------------------")

    # Verify that the original plan is still present
    assert "Definuj funkci `add(a, b)`" in plan

    # Verify that the generated code is correct
    assert "def add(a, b):" in code
    assert "return a + b" in code

    # Verify that the test results are as expected
    # The mock LLM should return a positive confirmation
    assert "Kód je funkční" in test_results

    # Verify that the ethical review is present
    assert 'ethical_review' in final_context.payload
    assert final_context.payload['ethical_review']
    assert "Ethical Review Feedback:" in final_context.payload['ethical_review']
