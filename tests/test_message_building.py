import pytest
from unittest.mock import patch, mock_open

# We need to import the class we are testing
from backend.sophia_chat_core import SophiaChatCore

# Mock data for our virtual files
MOCK_DNA = "DNA: I am Sophia."
MOCK_SYSTEM_PROMPT = "SYS: Follow these instructions."

@pytest.fixture
def chat_core_with_mocked_files():
    """
    Provides an instance of SophiaChatCore with a mocked file system,
    so we can test the file loading and message building logic in isolation.
    """
    mock_files = {
        "prompts/sophia/sophia_dna.txt": MOCK_DNA,
        "prompts/sophia/sophia_system_prompt.txt": MOCK_SYSTEM_PROMPT
    }
    def mock_open_logic(file, mode='r', encoding='utf-8'):
        if file in mock_files:
            return mock_open(read_data=mock_files[file])()
        else:
            raise FileNotFoundError(f"[Mock] File not found: {file}")

    # Patch file open, and also the dependencies we don't need for this test
    with patch("builtins.open", mock_open_logic), \
         patch('backend.sophia_chat_core.DatabaseManager'), \
         patch('backend.sophia_chat_core.LLMManager'):

        # This will now use the mocked `open` during its __init__
        yield SophiaChatCore()

def test_build_messages_structure(chat_core_with_mocked_files):
    """
    Tests if `_build_messages` creates a correctly structured list of dictionaries (messages).
    """
    # Arrange
    chat_core = chat_core_with_mocked_files
    mock_memories = ["memory 1"]
    mock_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]

    # Act
    messages = chat_core._build_messages(mock_memories, mock_history)

    # Assert
    # 1. It should be a list
    assert isinstance(messages, list)

    # 2. The first message should be the system message
    assert messages[0]["role"] == "system"
    assert MOCK_DNA in messages[0]["content"]
    assert MOCK_SYSTEM_PROMPT in messages[0]["content"]
    assert "memory 1" in messages[0]["content"]

    # 3. The following messages should be the conversation history
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "Hi there"

    # 4. Check the total number of messages
    assert len(messages) == 3
