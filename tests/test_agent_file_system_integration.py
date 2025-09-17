import unittest
import os
import shutil
from crewai import Task, Crew
import unittest.mock
from agents.engineer_agent import EngineerAgent
from tools.file_system import SANDBOX_DIR, FileSystemError, PathOutsideSandboxError
from core.llm_config import get_llm  # Import the factory function

class TestAgentFileSystemIntegration(unittest.TestCase):

    def setUp(self):
        """Set up a clean sandbox environment for each test."""
        # The get_llm() function will return a mock LLM because conftest.py
        # sets the SOPHIA_ENV='test' environment variable.
        llm = get_llm()
        engineer_wrapper = EngineerAgent(llm=llm)
        self.agent = engineer_wrapper.get_agent()

        # Ensure the sandbox directory exists and is clean
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR)

        # Define a test-specific subdirectory to avoid conflicts
        self.test_dir = os.path.join(SANDBOX_DIR, "integration_test_docs")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        """Clean up the sandbox after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_engineer_agent_can_write_file(self):
        """
        Tests if the Engineer Agent can successfully use the WriteFileTool.
        The test verifies the action (file creation), not the agent's final words,
        as the mock LLM is not designed for complex conversation.
        """
        test_file_path = os.path.join(self.test_dir, "agent_write_test.txt")
        test_content = "This file was written by an agent."

        task = Task(
            description=f"Use the Write File tool to create a file named '{test_file_path}' with the exact content: '{test_content}'.",
            expected_output="Confirmation of file creation.",
            agent=self.agent
        )

        Crew(agents=[self.agent], tasks=[task], verbose=False).kickoff()

        # Ground Truth Verification: Check if the file was actually created with the correct content.
        self.assertTrue(os.path.exists(test_file_path), "Agent should have created the file.")
        with open(test_file_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), test_content)

    def test_engineer_agent_can_read_file(self):
        """
        Tests if the Engineer Agent can successfully use the ReadFileTool and
        report the content in its final answer. This tests the full loop of
        action -> observation -> final answer.
        """
        test_file_path = os.path.join(self.test_dir, "agent_read_test.txt")
        test_content = "This is a readable test file."

        # Manually create the file that the agent will read.
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)

        task = Task(
            description=f"Use the Read File tool to read the file named '{test_file_path}' and state its content as your final answer.",
            expected_output="The final answer containing the file's content.",
            agent=self.agent
        )

        result = Crew(agents=[self.agent], tasks=[task], verbose=False).kickoff()

        # Verification: Check if the agent's final output contains the content of the file.
        # This works because our improved mock now echoes the tool output back in the final answer.
        self.assertIn(test_content, result.raw, "Agent's final answer should contain the file content.")

    @unittest.mock.patch('crewai.Crew.kickoff')
    def test_engineer_agent_run_task_handles_filesystem_error(self, mock_kickoff):
        """
        Tests if the EngineerAgent's run_task method correctly handles a
        FileSystemError raised by crew.kickoff() and re-raises it.
        This directly tests the try...except block in the wrapper.
        """
        # Configure the mock to raise a specific FileSystemError
        mock_kickoff.side_effect = PathOutsideSandboxError("Mocked kickoff failed as intended for test.")

        # Set up the agent and a dummy context
        llm = get_llm()
        engineer_wrapper = EngineerAgent(llm=llm)
        class DummyContext:
            payload = {'plan': "Any plan will do, as kickoff is mocked."}

        # Assert that calling run_task raises the expected exception
        with self.assertRaises(FileSystemError, msg="EngineerAgent.run_task should re-raise FileSystemError from kickoff."):
            engineer_wrapper.run_task(DummyContext())

        # Verify that kickoff was called once
        mock_kickoff.assert_called_once()


if __name__ == '__main__':
    unittest.main()
