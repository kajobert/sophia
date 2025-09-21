import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app
from services.websocket_manager import manager
import time
from unittest.mock import patch, MagicMock

# Use the TestClient for synchronous endpoints
client = TestClient(app)

@patch('main.Orchestrator')
@patch('main.GeminiLLMAdapter')
def test_create_task_and_get_status(MockLLMAdapter, MockOrchestrator):
    """
    Tests creating a task, then immediately polling its status.
    """
    # Arrange
    mock_llm_instance = MockLLMAdapter.return_value
    mock_orchestrator_instance = MockOrchestrator.return_value

    # Step 1: Create the task
    response_create = client.post("/api/v1/tasks", json={"prompt": "A simple test prompt"})
    assert response_create.status_code == 202
    task_id = response_create.json().get("task_id")
    assert task_id is not None

    # Allow some time for the background task to start and update the context
    time.sleep(1)

    # Step 2: Get the status of the created task
    response_status = client.get(f"/api/v1/tasks/{task_id}")
    assert response_status.status_code == 200
    status_data = response_status.json()
    assert status_data["task_id"] == task_id
    assert "status" in status_data
    assert "history" in status_data
    assert "feedback" in status_data

def test_get_task_status_not_found():
    """
    Tests that querying a non-existent task ID returns a 404 error.
    """
    response = client.get("/api/v1/tasks/a-non-existent-task-id")
    assert response.status_code == 404

@patch('main.Orchestrator')
@patch('main.GeminiLLMAdapter')
def test_websocket_communication(MockLLMAdapter, MockOrchestrator):
    """
    Tests the WebSocket endpoint by creating a task and listening for updates.
    """
    # Arrange
    # Mock the orchestrator to do nothing in the background initially
    mock_orchestrator_instance = MockOrchestrator.return_value
    mock_orchestrator_instance.execute_plan.return_value = None

    # Step 1: Create a task to get a valid task_id
    response_create = client.post("/api/v1/tasks", json={"prompt": "Test websocket communication"})
    assert response_create.status_code == 202
    task_id = response_create.json().get("task_id")
    assert task_id is not None

    # Step 2: Connect to the WebSocket and listen for messages
    with client.websocket_connect(f"/api/v1/tasks/{task_id}/ws") as websocket:
        # Manually trigger a broadcast after connection is established
        # In a real scenario, this would be done by the orchestrator in a background thread
        test_message = {"type": "step_update", "step_id": 1, "description": "Test Step", "status": "success", "output": "Success"}

        # We need to run the broadcast in an event loop
        async def do_broadcast():
            await manager.broadcast(test_message, task_id)

        asyncio.run(do_broadcast())

        # Receive the message
        data = websocket.receive_json()

        # Verify the structure of the received message
        assert data == test_message
