from typing import Any, List, Optional, Dict
from langchain_core.language_models.llms import LLM

class MockGeminiLLMAdapter(LLM):
    """
    A mock LLM adapter for testing. It is compatible with LangChain and crewAI.
    Its primary role is to act as a placeholder type for the test environment.
    The actual mocking of LLM calls is handled by a monkeypatch in conftest.py.
    """
    model_name: str = "mock-gemini-for-crewai"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        This method should not be called directly in the context of crewAI,
        as the actual calls are intercepted by the monkeypatch in conftest.py.
        """
        raise NotImplementedError(
            "This mock adapter is not meant to be called directly. "
            "The mocking is handled by monkeypatching `litellm.completion` in tests."
        )

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "mock_gemini_llm_adapter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {"model_name": self.model_name}
