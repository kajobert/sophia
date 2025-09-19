import pytest
import os

@pytest.fixture(scope="function", autouse=True)
def set_test_mode_for_function(monkeypatch):
    """
    Ensures that the SOPHIA_TEST_MODE environment variable is set to "1"
    for the entire test session, before any modules are imported.
    This is critical for tests that rely on this variable to mock services
    like Redis or LLM calls at import time.
    """
    monkeypatch.setenv("SOPHIA_TEST_MODE", "1")
