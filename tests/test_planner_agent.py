import unittest
from unittest.mock import patch, MagicMock
from crewai import Task

class TestPlannerAgent(unittest.TestCase):

    # Decorators are applied from bottom up.
    # 1. os.getenv is patched.
    # 2. ChatGoogleGenerativeAI is patched.
    # 3. Agent.execute_task is patched.
    @unittest.skip("Dočasně skipnuto: metaclass conflict v langchain_google_genai - viz https://github.com/langchain-ai/langchain-google-genai/issues/70")
    @patch('crewai.agent.Agent.execute_task')
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    @patch('os.getenv')
    def test_planner_agent_execution(self, mock_getenv, mock_chat_google, mock_execute_task):
        # --- Setup Mocks ---
        # Mock dependencies to allow the agent module to be imported without error.
        mock_getenv.return_value = "DUMMY_API_KEY"
        mock_chat_google.return_value = MagicMock()

        # Mock the agent's execution method to return a predictable string.
        # This is the method called by task.execute().
        mock_execute_task.return_value = "Mock plan generated successfully."

        # --- Import Agent ---
        # This import must happen *after* the mocks are in place.
        from agents.planner_agent import PlannerAgent

        # --- Create Task ---
        # Create a task and assign it to the agent.
        task = Task(
            description="Create a plan for a new feature.",
            agent=PlannerAgent,
            expected_output="A comprehensive plan."
        )

        # --- Execute and Assert ---
        # Calling task.execute() will now call our mocked Agent.execute_task
        result = task.execute()

        # Assert that the result is the one from our mock.
        self.assertEqual(result, "Mock plan generated successfully.")

        # Assert that the mocked execution method was called exactly once.
        mock_execute_task.assert_called_once()

if __name__ == '__main__':
    unittest.main()
