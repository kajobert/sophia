import asyncio
from services.websocket_manager import manager
from unittest.mock import patch, AsyncMock


@patch("main.neocortex", new_callable=AsyncMock)
def test_create_task_and_get_status(mock_neocortex, client):
    """
    Tests creating a task, then immediately polling its status.
    """
    # Arrange
    # The background task is mocked, so we don't need to check for its completion.

    # Step 1: Create the task
    response_create = client.post(
        "/api/v1/tasks", json={"prompt": "A simple test prompt"}
    )
    assert response_create.status_code == 202
    task_id = response_create.json().get("task_id")
    assert task_id is not None

    # Check that the neocortex was called
    mock_neocortex.process_input.assert_called_once_with(
        session_id=task_id, user_input="A simple test prompt"
    )

    # Step 2: Get the status of the created task
    # Since the neocortex is mocked, the STM won't have any state. We expect a 404.
    # A more advanced test could also mock main.stm.
    response_status = client.get(f"/api/v1/tasks/{task_id}")
    assert response_status.status_code == 404


def test_get_task_status_not_found(client):
    """
    Tests that querying a non-existent task ID returns a 404 error.
    """
    response = client.get("/api/v1/tasks/a-non-existent-task-id")
    assert response.status_code == 404


@patch("main.neocortex", new_callable=AsyncMock)
def test_websocket_communication(mock_neocortex, client):
    """
    Tests the WebSocket endpoint by creating a task and listening for updates.
    """
    # Arrange
    # The neocortex is already mocked by the decorator.
    # We can configure its behavior if needed.
    mock_neocortex.process_input.return_value = None

    # Step 1: Create a task to get a valid task_id
    response_create = client.post(
        "/api/v1/tasks", json={"prompt": "Test websocket communication"}
    )
    assert response_create.status_code == 202
    task_id = response_create.json().get("task_id")
    assert task_id is not None

    # Step 2: Connect to the WebSocket and listen for messages
    with client.websocket_connect(f"/api/v1/tasks/{task_id}/ws") as websocket:
        # Manually trigger a broadcast after connection is established
        # In a real scenario, this would be done by the orchestrator in a background thread
        test_message = {
            "type": "step_update",
            "step_id": 1,
            "description": "Test Step",
            "status": "success",
            "output": "Success",
        }

        # We need to run the broadcast in an event loop
        async def do_broadcast():
            await manager.broadcast(test_message, task_id)

        asyncio.run(do_broadcast())

        # Receive the message
        data = websocket.receive_json()

        # Verify the structure of the received message
        assert data == test_message
