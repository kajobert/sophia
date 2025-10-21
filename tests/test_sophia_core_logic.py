import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Mock dependencies before importing the class that uses them
from backend.database_manager import DatabaseManager
from core.llm_manager import LLMManager

# Mock the actual classes
DatabaseManager = MagicMock()
LLMManager = MagicMock()

# Now import the class we want to test
from backend.sophia_chat_core import SophiaChatCore

@pytest.mark.asyncio
async def test_handle_message_with_mocked_successful_llm_call():
    """
    Tests the full logic of handle_message by mocking a successful LLM response.
    This simulates the exact scenario from the user's log.
    """
    # 1. Arrange: Set up all the mocks

    # Mock the successful response object from the openai library
    # This structure mimics a real `ChatCompletion` object.
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a successful test response."

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [mock_choice]

    # Mock the LLM adapter
    mock_llm_adapter = MagicMock()
    # The key method `generate_content_async` must be an AsyncMock to be awaitable
    mock_llm_adapter.generate_content_async = AsyncMock(return_value=(mock_llm_response, {"usage": "mock"}))

    # Mock the LLMManager to return our mock adapter
    mock_llm_manager_instance = LLMManager()
    mock_llm_manager_instance.get_llm.return_value = mock_llm_adapter

    # Mock the DatabaseManager
    mock_db_manager_instance = DatabaseManager()
    mock_db_manager_instance.get_recent_messages.return_value = []
    mock_db_manager_instance.query_memory.return_value = []

    # 2. Act: Instantiate SophiaChatCore and call the method

    chat_core = SophiaChatCore()
    # Manually inject the mocked instances
    chat_core.db_manager = mock_db_manager_instance
    chat_core.llm_manager = mock_llm_manager_instance

    session_id = "test_session"
    user_message = "test"

    response_text = await chat_core.handle_message(session_id, user_message)

    # 3. Assert: Check if the logic behaved as expected

    # Check that the correct methods on our mocks were called
    mock_llm_manager_instance.get_llm.assert_called_once_with("powerful")
    mock_llm_adapter.generate_content_async.assert_called_once()

    # Check that the database was updated with both user and assistant messages
    assert mock_db_manager_instance.add_message.call_count == 2
    mock_db_manager_instance.add_message.assert_any_call(session_id, 'user', user_message)
    mock_db_manager_instance.add_message.assert_any_call(session_id, 'assistant', "This is a successful test response.")

    # Crucially, check that the final returned text is correct
    assert response_text == "This is a successful test response."
