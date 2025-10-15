import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from memory.advanced_memory import AdvancedMemory
from tools.memory_tools import MemoryReaderTool
from datetime import datetime
import json
import asyncio


class TestAdvancedMemory(unittest.TestCase):
    @patch("memory.advanced_memory.Memori")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""
database:
  db_host: "mock_host"
  db_port: 5432
  db_user: "mock_user"
  db_password: "mock_password"
  db_name: "mock_db"
""",
    )
    def setUp(self, mock_file, MockMemori):
        self.mock_memori_instance = MockMemori.return_value
        self.mock_session = MagicMock()
        self.mock_memori_instance.db_manager.SessionLocal.return_value = (
            self.mock_session
        )
        self.memory = AdvancedMemory()

    def test_initialization(self):
        self.mock_memori_instance.enable.assert_called_once()

    def test_add_task_with_verification(self):
        async def run_test():
            self.mock_memori_instance.record_conversation.return_value = "chat_123"
            self.mock_session.execute.return_value.fetchone.side_effect = [
                None,
                ("chat_123",),
            ]
            task_id = await self.memory.add_task("Test task with verification")
            self.assertEqual(task_id, "chat_123")
            self.assertEqual(self.mock_session.execute.call_count, 2)

        asyncio.run(run_test())

    def test_add_task_timeout(self):
        async def run_test():
            self.mock_memori_instance.record_conversation.return_value = "chat_456"
            self.mock_session.execute.return_value.fetchone.return_value = None
            with self.assertRaises(TimeoutError):
                await self.memory.add_task("Test task timeout")

        with patch("time.time", side_effect=[0, 1, 2, 3, 4, 5, 6]):
            asyncio.run(run_test())

    def test_get_next_task(self):
        async def run_test():
            self.mock_session.execute.return_value.fetchone.return_value = ("task_456",)
            self.mock_memori_instance.get_conversation_history.return_value = [
                {
                    "chat_id": "task_456",
                    "user_input": "A new task",
                    "metadata": {"status": "IN_PROGRESS"},
                }
            ]
            task = await self.memory.get_next_task()
            self.assertIsNotNone(task)
            self.assertEqual(task["chat_id"], "task_456")
            self.assertEqual(task["metadata"]["status"], "IN_PROGRESS")
            self.assertGreaterEqual(
                self.mock_memori_instance.db_manager.SessionLocal.call_count, 1
            )

        asyncio.run(run_test())

    def test_update_task_status(self):
        async def run_test():
            self.mock_memori_instance.get_conversation_history.return_value = [
                {"chat_id": "task_789", "metadata": {"status": "IN_PROGRESS"}}
            ]
            await self.memory.update_task_status("task_789", "DONE")
            self.mock_memori_instance.db_manager.SessionLocal.assert_called_once()
            self.mock_session.execute.assert_called_once()
            self.mock_session.commit.assert_called_once()
            self.mock_session.close.assert_called_once()

        asyncio.run(run_test())

    @patch("tools.memory_tools.AdvancedMemory")
    def test_memory_reader_tool_arun(self, MockAdvancedMemory):
        async def run_test():
            mock_memory_instance = MockAdvancedMemory.return_value
            test_time = datetime(2025, 1, 1, 12, 30, 0)
            mock_memory_instance.read_last_n_memories = AsyncMock(
                return_value=[
                    {
                        "chat_id": "1",
                        "timestamp": test_time,
                        "user_input": "Test with datetime",
                    }
                ]
            )
            tool = MemoryReaderTool()
            result_json = await tool._arun(n=1)
            result_data = json.loads(result_json)
            self.assertEqual(len(result_data), 1)
            self.assertEqual(result_data[0]["timestamp"], test_time.isoformat())
            mock_memory_instance.read_last_n_memories.assert_called_once_with(
                n=1, mem_type=None
            )

        asyncio.run(run_test())

    @patch("tools.memory_tools.AdvancedMemory")
    def test_memory_reader_tool_run(self, MockAdvancedMemory):
        mock_memory_instance = MockAdvancedMemory.return_value
        test_time = datetime(2025, 1, 1, 12, 30, 0)
        # We need to mock the async method, as _run will call it
        mock_memory_instance.read_last_n_memories = AsyncMock(
            return_value=[
                {
                    "chat_id": "1",
                    "timestamp": test_time,
                    "user_input": "Test with datetime",
                }
            ]
        )
        tool = MemoryReaderTool()
        # Call the synchronous _run method
        result_json = tool._run(n=1)
        result_data = json.loads(result_json)
        self.assertEqual(len(result_data), 1)
        self.assertEqual(result_data[0]["timestamp"], test_time.isoformat())
        mock_memory_instance.read_last_n_memories.assert_called_once_with(
            n=1, mem_type=None
        )


if __name__ == "__main__":
    unittest.main()
