import pytest
from unittest.mock import patch, mock_open
from backend.sophia_chat_core import SophiaChatCore

# Mock data to be "read" from the virtual files
MOCK_DNA = "DNA: I am Sophia."
MOCK_SYSTEM_PROMPT = "SYS: Follow these instructions."

@pytest.fixture
def mock_file_system():
    """
    Mocks the built-in `open` function to simulate reading from our prompt files
    without actually touching the disk.
    """
    # Define a dictionary for our virtual file system
    mock_files = {
        "prompts/sophia/sophia_dna.txt": MOCK_DNA,
        "prompts/sophia/sophia_system_prompt.txt": MOCK_SYSTEM_PROMPT
    }

    # Create a mock for the `open` function that checks the file path
    # and returns the corresponding content.
    def mock_open_logic(file, mode='r', encoding='utf-8'):
        if file in mock_files:
            return mock_open(read_data=mock_files[file])()
        else:
            raise FileNotFoundError(f"[Mock] File not found: {file}")

    # Use patch to replace the real `open` with our mock
    with patch("builtins.open", mock_open_logic):
        yield

def test_sophia_core_loads_prompts_on_init(mock_file_system):
    """
    Tests if SophiaChatCore correctly loads the DNA and system prompt
    from files during its initialization.
    """
    # Patch the other dependencies so we only test the file loading
    with patch('backend.sophia_chat_core.DatabaseManager'), \
         patch('backend.sophia_chat_core.LLMManager'):

        chat_core = SophiaChatCore()

        assert chat_core.sophia_dna == MOCK_DNA
        assert chat_core.system_prompt == MOCK_SYSTEM_PROMPT

def test_build_prompt_assembles_correctly(mock_file_system):
    """
    Tests if the `_build_prompt` method correctly assembles all parts
    into the final prompt string.
    """
    with patch('backend.sophia_chat_core.DatabaseManager'), \
         patch('backend.sophia_chat_core.LLMManager'):

        chat_core = SophiaChatCore()

        # Define mock context
        mock_memories = ["memory 1", "memory 2"]
        mock_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

        # Call the method to be tested
        final_prompt = chat_core._build_prompt(mock_memories, mock_history)

        # Check that all parts are present in the final string
        assert MOCK_DNA in final_prompt
        assert MOCK_SYSTEM_PROMPT in final_prompt
        assert "RELEVANT MEMORIES" in final_prompt
        assert "memory 1" in final_prompt
        assert "CURRENT CONVERSATION HISTORY" in final_prompt
        assert "User: Hello" in final_prompt
        assert "Sophia: Hi there" in final_prompt
        assert "YOUR TASK" in final_prompt
