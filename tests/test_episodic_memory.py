import unittest
from unittest.mock import patch, MagicMock, mock_open
from memory.episodic_memory import EpisodicMemory
from tools.memory_tools import EpisodicMemoryReaderTool
from datetime import datetime
import json

class TestEpisodicMemory(unittest.TestCase):

    @patch('psycopg2.connect')
    @patch('builtins.open', new_callable=mock_open, read_data="""
database:
  db_host: "mock_host"
  db_port: 5432
  db_user: "mock_user"
  db_password: "mock_password"
  db_name: "mock_db"
""")
    def setUp(self, mock_file, mock_connect):
        """
        Set up a mock database connection before each test.
        """
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        self.memory = EpisodicMemory()

    def test_initialization(self):
        """
        Test that the database connection and table creation are called on initialization.
        """
        self.mock_conn.cursor.assert_called_once()
        self.mock_cursor.execute.assert_called_once_with(unittest.mock.ANY) # Checks for CREATE TABLE
        self.mock_conn.commit.assert_called_once()

    def test_add_memory(self):
        """
        Test the add_memory method.
        """
        self.mock_cursor.fetchone.return_value = (1,) # Mock the RETURNING id

        memory_id = self.memory.add_memory("Test content", "test_type")

        self.assertEqual(memory_id, 1)
        self.mock_cursor.execute.assert_called_with(unittest.mock.ANY, unittest.mock.ANY)
        self.assertEqual(self.mock_cursor.execute.call_args[0][0].strip().startswith("INSERT INTO memories"), True)
        self.mock_conn.commit.assert_called()

    def test_access_memory(self):
        """
        Test the access_memory method.
        """
        # Mock the initial SELECT call
        self.mock_cursor.fetchone.return_value = (1, "2025-01-01", "content", "type", 1.0, 0.0)

        memory_data = self.memory.access_memory(1)

        self.assertIsNotNone(memory_data)
        self.assertEqual(memory_data['weight'], 1.1)

        # Check that __init__ (CREATE), SELECT, and UPDATE were called
        self.assertEqual(self.mock_cursor.execute.call_count, 3)
        self.assertEqual(self.mock_cursor.execute.call_args_list[1][0][0].strip().startswith("SELECT"), True)
        self.assertEqual(self.mock_cursor.execute.call_args_list[2][0][0].strip().startswith("UPDATE"), True)

    def test_get_next_task(self):
        """
        Test the get_next_task method.
        """
        # Mock the SELECT for a new task
        self.mock_cursor.fetchone.side_effect = [
            (10, "2025-01-01", "New Task", "NEW_TASK", 1.0, 0.0), # First find
            (10, "2025-01-01", "New Task", "IN_PROGRESS", 1.0, 0.0) # Second find after update
        ]

        task = self.memory.get_next_task()

        self.assertIsNotNone(task)
        self.assertEqual(task['id'], 10)
        self.assertEqual(task['type'], 'IN_PROGRESS')

        # Check for __init__ (CREATE), SELECT, UPDATE, SELECT
        self.assertEqual(self.mock_cursor.execute.call_count, 4)

    def tearDown(self):
        """
        Close the connection after each test.
        """
        self.memory.close()
        self.mock_conn.close.assert_called_once()

    @patch('tools.memory_tools.EpisodicMemory')
    def test_memory_serialization(self, MockEpisodicMemory):
        """
        Test that the EpisodicMemoryReaderTool correctly serializes datetime objects.
        """
        # Vytvoření instance mocku a nastavení návratové hodnoty
        mock_memory_instance = MockEpisodicMemory.return_value
        test_time = datetime(2025, 1, 1, 12, 30, 0)
        mock_memory_instance.read_last_n_memories.return_value = [{
            "id": 1,
            "timestamp": test_time,
            "content": "Test with datetime",
            "type": "test",
            "weight": 1.0,
            "ethos_coefficient": 0.0
        }]

        # Spuštění nástroje
        tool = EpisodicMemoryReaderTool()
        result_json = tool._run(n=1)

        # Ověření, že výstup je validní JSON a obsahuje správně naformátovaný čas
        try:
            result_data = json.loads(result_json)
            self.assertEqual(len(result_data), 1)
            self.assertEqual(result_data[0]['timestamp'], test_time.isoformat())
        except json.JSONDecodeError:
            self.fail("The output of the tool is not a valid JSON string.")


if __name__ == '__main__':
    unittest.main()
