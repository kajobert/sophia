import unittest
import asyncio
from unittest.mock import patch, MagicMock
from mcp_servers.worker.jules_api_server import get_jules_task_status, get_jules_task_result
import json

class TestJulesApiServer(unittest.TestCase):

    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    @patch.dict('os.environ', {'JULES_API_KEY': 'test_key'})
    def test_get_jules_task_status_success(self, mock_client):
        async def run_test():
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "in_progress"}

            mock_async_client = MagicMock()
            mock_async_client.get.return_value = asyncio.Future()
            mock_async_client.get.return_value.set_result(mock_response)

            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await get_jules_task_status(task_id="123")
            result_json = json.loads(result)

            self.assertEqual(result_json, {"status": "in_progress"})
            mock_async_client.get.assert_called_once_with(
                "https://jules.googleapis.com/v1alpha/sessions/123",
                headers={'X-Goog-Api-Key': 'test_key'},
                timeout=30.0
            )

        asyncio.run(run_test())

    @patch.dict('os.environ', {}, clear=True)
    def test_get_jules_task_status_no_api_key(self):
        async def run_test():
            result = await get_jules_task_status(task_id="123")
            result_json = json.loads(result)
            self.assertEqual(result_json, {"error": "JULES_API_KEY is not configured."})

        asyncio.run(run_test())

    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    @patch.dict('os.environ', {'JULES_API_KEY': 'test_key'})
    def test_get_jules_task_result_success(self, mock_client):
        async def run_test():
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "task completed successfully"}

            mock_async_client = MagicMock()
            mock_async_client.get.return_value = asyncio.Future()
            mock_async_client.get.return_value.set_result(mock_response)

            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await get_jules_task_result(task_id="123")
            result_json = json.loads(result)

            self.assertEqual(result_json, {"result": "task completed successfully"})
            mock_async_client.get.assert_called_once_with(
                "https://jules.googleapis.com/v1alpha/sessions/123/result",
                headers={'X-Goog-Api-Key': 'test_key'},
                timeout=60.0
            )

        asyncio.run(run_test())

    @patch.dict('os.environ', {}, clear=True)
    def test_get_jules_task_result_no_api_key(self):
        async def run_test():
            result = await get_jules_task_result(task_id="123")
            result_json = json.loads(result)
            self.assertEqual(result_json, {"error": "JULES_API_KEY is not configured."})

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()