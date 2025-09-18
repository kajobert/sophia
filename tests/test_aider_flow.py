import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from web.api import app

class TestAiderFlow(unittest.TestCase):
    def setUp(self):
        self.test_file_path = "sandbox/test_file.txt"
        # Ensure sandbox directory exists and create a dummy file for tests
        os.makedirs(os.path.dirname(self.test_file_path), exist_ok=True)
        with open(self.test_file_path, "w") as f:
            f.write("Initial content.")

    def tearDown(self):
        # Clean up the dummy file
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    @patch('agents.aider_agent.AiderAgent.propose_change')
    def test_chat_routes_to_aider_agent_on_modify_command(self, mock_propose_change):
        """
        Tests that a prompt with the 'modify file' command is correctly
        routed to the AiderAgent. Using the TestClient as a context manager
        ensures that the application's lifespan events (startup/shutdown) are handled.
        """
        # Arrange
        mock_propose_change.return_value = {"status": "success", "message": "Change proposed by mock."}
        prompt = f"modify file `{self.test_file_path}`: a new line of text"

        # Act
        with TestClient(app) as client:
            response = client.post("/chat", json={"prompt": prompt})

        # Assert
        # 1. Check API response
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['status'], 'success')
        self.assertIn('aider_result', response_json['final_context'])

        # 2. Check that AiderAgent.propose_change was called correctly
        mock_propose_change.assert_called_once()
        call_args, call_kwargs = mock_propose_change.call_args
        self.assertEqual(call_args, ()) # Assert it was called with no positional args
        self.assertEqual(call_kwargs.get('description'), "a new line of text")
        self.assertEqual(call_kwargs.get('files'), [self.test_file_path])

    def test_chat_routes_to_standard_flow_on_normal_prompt(self):
        """
        Tests that a normal prompt is routed to the standard orchestration flow.
        """
        # Arrange
        prompt = "Tell me a joke."

        # Act
        with TestClient(app) as client:
            response = client.post("/chat", json={"prompt": prompt})

        # Assert
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['status'], 'success')
        # In the standard flow, we expect a 'plan', not 'aider_result'
        self.assertIn('plan', response_json['final_context'])
        self.assertNotIn('aider_result', response_json['final_context'])
