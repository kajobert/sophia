import pytest
from core.gemini_llm_adapter import GeminiLLMAdapter
import os

def test_gemini_llm_adapter_init():
    # Dummy API key, won't actually call API
    adapter = GeminiLLMAdapter(model="gemini-2.5-flash", api_key="dummy-key", temperature=0.7, max_tokens=128)
    assert adapter.model_name == "gemini-2.5-flash"
    assert adapter.api_key == "dummy-key"
    assert adapter.temperature == 0.7
    assert adapter.max_tokens == 128

def test_gemini_llm_adapter_call_mock(monkeypatch):
    # Mock the actual Gemini API call
    adapter = GeminiLLMAdapter(model="gemini-2.5-flash", api_key="dummy-key", temperature=0.7, max_tokens=32)

    class DummyResponse:
        def __init__(self):
            self.text = "Hello, Sophia!"
            self.usage_metadata = {"total_tokens": 7}

    def dummy_generate(self, prompt, generation_config):
        return DummyResponse()

    monkeypatch.setattr(GeminiLLMAdapter, "_generate", dummy_generate)
    result = adapter("Say hello to Sophia")
    assert "Hello, Sophia" in result
    assert adapter.get_token_usage() == 7

def test_gemini_llm_token_usage():
    adapter = GeminiLLMAdapter(model="gemini-2.5-flash", api_key="dummy-key", temperature=0.7, max_tokens=32)
    adapter._last_token_usage = 42
    assert adapter.get_token_usage() == 42
