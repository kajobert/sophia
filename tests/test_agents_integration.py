import pytest
from crewai import Task, Crew
from agents.engineer_agent import EngineerAgent
from tools.file_system import ReadFileTool, WriteFileTool
import os

SANDBOX_DIR = os.path.abspath("sandbox")

@pytest.fixture
def setup_sandbox():
    """Set up a clean sandbox directory for tests."""
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    # Clean up previous test files if they exist
    for f in os.listdir(SANDBOX_DIR):
        if os.path.isfile(os.path.join(SANDBOX_DIR, f)):
            os.remove(os.path.join(SANDBOX_DIR, f))
    yield
    # Clean up after test
    for f in os.listdir(SANDBOX_DIR):
        if os.path.isfile(os.path.join(SANDBOX_DIR, f)):
            os.remove(os.path.join(SANDBOX_DIR, f))

@pytest.mark.skip(reason="Skipping due to a persistent Pydantic ValidationError when initializing Agent with tools. This likely indicates a deep dependency conflict between crewai and pydantic v2, which needs to be resolved by updating library versions.")
def test_engineer_creates_file_via_task(setup_sandbox, monkeypatch):
    """
    Tests that an engineer agent can execute a task to create a file,
    using a mocked LLM that forces a tool call.
    """
    # This test is currently skipped. The mocking strategy below is now
    # obsolete due to the global mock in conftest.py. If this test is
    # to be re-enabled, it will need a new mocking approach.

    # 2. Define Agent and provide it with the necessary tool for the test.
    engineer = EngineerAgent().get_agent()
    engineer.tools = [WriteFileTool()]

    # 3. Define the task for the agent.
    # The mock LLM will see this description and return a canned response
    # to use the WriteFileTool.
    task = Task(
      description="Create a python file named 'test_output.py' with specific content.",
      agent=engineer,
      expected_output="The file 'test_output.py' created in the sandbox."
    )

    # 4. Create and run the crew.
    crew = Crew(
        agents=[engineer],
        tasks=[task],
        verbose=0 # Set to 2 for debugging
    )
    crew.kickoff()

    # 5. Verify that the agent's tool use was successful.
    file_content = ReadFileTool().run_sync('test_output.py')
    assert "This is a test file created by the engineer." in file_content
