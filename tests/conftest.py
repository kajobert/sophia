import pytest
import os
from core.mocks import mock_litellm_completion_handler

def pytest_configure(config):
    """
    This hook runs at the beginning of the test session. It sets the
    environment variable to 'test' so the factory provides the mock adapter.
    """
    os.environ['SOPHIA_ENV'] = 'test'
    print("\n--- SOPHIA_ENV set to 'test' via pytest_configure ---")

class MockAdvancedMemory:
    """A mock class to prevent real database connections during tests."""
    def __init__(self, config_path='config.yaml', user_id="sophia"):
        print("--- MockAdvancedMemory initialized ---")

    async def add_memory(self, content, mem_type, metadata=None):
        print(f"--- Mocked add_memory called with content: '{content}' ---")
        return "mock_chat_id_12345"

    def close(self):
        print("--- MockAdvancedMemory closed ---")
        pass

@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch):
    """
    This fixture automatically mocks all external services for every test.
    - Mocks LLM calls (`litellm.completion` and `litellm.acompletion`).
    - Mocks `AdvancedMemory` to prevent real database connections.
    """
    # Mock LLM calls
    monkeypatch.setattr("litellm.completion", mock_litellm_completion_handler)
    monkeypatch.setattr("litellm.acompletion", mock_litellm_completion_handler)
    print("--- `litellm.completion` and `acompletion` have been monkeypatched ---")

    # Mock AdvancedMemory to prevent real database connections
    monkeypatch.setattr("memory.advanced_memory.AdvancedMemory", MockAdvancedMemory)
    print("--- `AdvancedMemory` has been monkeypatched ---")
