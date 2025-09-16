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

@pytest.fixture(autouse=True)
def mock_llm_calls(monkeypatch):
    """
    This fixture automatically mocks `litellm.completion` for every test
    using the centralized handler from core.mocks.
    """
    monkeypatch.setattr("litellm.completion", mock_litellm_completion_handler)
    monkeypatch.setattr("litellm.acompletion", mock_litellm_completion_handler)
    print("--- `litellm.completion` has been monkeypatched with handler from core.mocks ---")
