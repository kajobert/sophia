import unittest
from unittest.mock import patch, MagicMock, mock_open
from memory.advanced_memory import AdvancedMemory
from tools.memory_tools import MemoryReaderTool
from datetime import datetime
import json

class TestAdvancedMemory(unittest.TestCase):

    @patch('memory.advanced_memory.Memori')
    @patch('builtins.open', new_callable=mock_open, read_data="""
database:
  db_host: "mock_host"
  db_port: 5432
  db_user: "mock_user"
  db_password: "mock_password"
  db_name: "mock_db"
""")
    def setUp(self, mock_file, MockMemori):
        """
        Set up a mock Memori instance before each test.
        """
        self.mock_memori_instance = MockMemori.return_value
        self.memory = AdvancedMemory()

    def test_initialization(self):
        """
        Test that the Memori library is initialized on startup.
        """
        self.mock_memori_instance.enable.assert_called_once()

    def test_add_memory(self):
        """
        Test the add_memory method.
        """
        self.mock_memori_instance.record_conversation.return_value = "chat_123"

        memory_id = self.memory.add_memory("Test content", "test_type")

        self.assertEqual(memory_id, "chat_123")
        self.mock_memori_instance.record_conversation.assert_called_once_with(
            user_input="Test content",
            ai_output="Noted: test_type",
            model="internal_event",
            metadata={'memory_type': 'test_type'}
        )

    def test_get_next_task(self):
        """
        Test the get_next_task method.
        """
        # Mock the search_memories call to return a new task
        self.mock_memori_instance.db_manager.search_memories.return_value = [{
            'chat_id': 'task_456',
            'timestamp': datetime.now(),
            'metadata': {'status': 'new'}
        }]

        # Mock the access_memory call that happens after the update
        self.mock_memori_instance.get_conversation_history.return_value = [{
            'chat_id': 'task_456',
            'user_input': 'A new task',
            'metadata': {'status': 'IN_PROGRESS'}
        }]

        task = self.memory.get_next_task()

        self.assertIsNotNone(task)
        self.assertEqual(task['chat_id'], 'task_456')
        self.assertEqual(task['metadata']['status'], 'IN_PROGRESS')

        # Check that search_memories and execute_with_translation were called
        self.mock_memori_instance.db_manager.search_memories.assert_called_once()
        self.mock_memori_instance.db_manager.execute_with_translation.assert_called_once()

    def test_update_task_status(self):
        """
        Test the update_task_status method.
        """
        # Mock the access_memory call
        self.mock_memori_instance.get_conversation_history.return_value = [{
            'chat_id': 'task_789',
            'metadata': {'status': 'IN_PROGRESS'}
        }]

        self.memory.update_task_status('task_789', 'DONE')

        self.mock_memori_instance.db_manager.execute_with_translation.assert_called_once()
        call_args = self.mock_memori_instance.db_manager.execute_with_translation.call_args
        self.assertIn("UPDATE chat_history", str(call_args.args[0]))
        self.assertIn("'status': '\"DONE\"'", str(call_args.kwargs))


    @patch('tools.memory_tools.AdvancedMemory')
    def test_memory_reader_tool(self, MockAdvancedMemory):
        """
        Test that the MemoryReaderTool correctly calls the AdvancedMemory.
        """
        mock_memory_instance = MockAdvancedMemory.return_value
        test_time = datetime(2025, 1, 1, 12, 30, 0)
        mock_memory_instance.read_last_n_memories.return_value = [{
            "chat_id": "1",
            "timestamp": test_time,
            "user_input": "Test with datetime",
        }]

        tool = MemoryReaderTool()
        result_json = tool._run(n=1)

        # Ověření, že výstup je validní JSON a obsahuje správně naformátovaný čas
        try:
            result_data = json.loads(result_json)
            self.assertEqual(len(result_data), 1)
            self.assertEqual(result_data[0]['timestamp'], test_time.isoformat())
            mock_memory_instance.read_last_n_memories.assert_called_once_with(1)
        except json.JSONDecodeError:
            self.fail("The output of the tool is not a valid JSON string.")


if __name__ == '__main__':
    unittest.main()
