import pytest
from unittest.mock import patch
from crewai import Crew, Task
from agents.planner_agent import PlannerAgent


@patch("crewai.memory.storage.kickoff_task_outputs_storage.sqlite3.connect")
@patch(
    "crewai.agent.Agent.execute_task",
    return_value="Mocked plan generated successfully.",
)
def test_planner_agent_execution_in_crew(mock_agent_execute, mock_sqlite_connect):
    """
    Tests the planner agent's execution within a Crew by mocking the agent's
    execute_task method. This validates that the Crew and Task are wired
    correctly to the agent without needing a real LLM.
    Also mocks sqlite3.connect to prevent CrewAI from creating a DB.
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
    # We don't need to assert the number of sqlite calls, just that our mock was effective.
    assert mock_sqlite_connect.called
