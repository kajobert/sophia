
from unittest.mock import patch
from conftest import robust_import, safe_remove

# Robustní import crewai
crewai = robust_import('crewai')
from crewai import Crew, Task
from agents.planner_agent import PlannerAgent


@patch(
    "crewai.agent.Agent.execute_task",
    return_value="Mocked plan generated successfully.",
)
def test_planner_agent_execution_in_crew(mock_agent_execute):
    """
    Tests the planner agent's execution within a Crew by mocking the agent's
    execute_task method. This validates that the Crew and Task are wired
    correctly to the agent without needing a real LLM.
    """
    # 1. Since execute_task is mocked, the LLM is never called.
    # We can initialize the agent with a dummy LLM object (None).
    planner_instance = PlannerAgent(llm=None).get_agent()

    # 2. Create a task for the agent
    task = Task(
        description="Create a plan for a new feature.",
        agent=planner_instance,
        expected_output="A comprehensive plan.",
    )

    # 3. Create and run the Crew
    crew = Crew(agents=[planner_instance], tasks=[task], verbose=0)
    result = crew.kickoff()

    # 4. Assert the result
    # The result of kickoff() is a CrewOutput object; the raw string is in the .raw attribute.
    assert result.raw == "Mocked plan generated successfully."
    mock_agent_execute.assert_called_once()
