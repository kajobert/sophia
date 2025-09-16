from typing import Any, List, Optional, Dict
from langchain_core.language_models.llms import LLM
from litellm.utils import ModelResponse, Choices, Message

def mock_litellm_completion_handler(*args, **kwargs) -> ModelResponse:
    """
    A centralized mock handler for litellm.completion.
    It inspects the prompt and returns a canned response suitable for tests,
    ensuring consistent mock behavior across pytest and the Uvicorn server.
    """
    messages = kwargs.get("messages", [])
    prompt = ""
    if messages:
        # The relevant prompt is usually the last message in the list
        prompt = messages[-1].get("content", "")

    prompt_lower = prompt.lower()

    response_content = ""
    if "otestuj" in prompt_lower or "test" in prompt_lower:
        response_content = "Thought: The user wants me to test the code. I will confirm it's functional.\nFinal Answer: Kód je funkční a splňuje všechny požadavky."
    elif "kód" in prompt_lower or "code" in prompt_lower:
        response_content = "Thought: The user wants code based on the plan. I will provide a Python code block.\nFinal Answer:\n```python\ndef add(a, b):\n  # This function adds two numbers\n  return a + b\n```"
    elif "plán" in prompt_lower or "plan" in prompt_lower:
        if "ethical review" in prompt_lower or "etickou revizi" in prompt_lower:
            response_content = "Thought: The user wants a plan and an ethical review.\nFinal Answer:\nToto je jednoduchý plán:\n1. Definuj funkci `add(a, b)`.\n2. Funkce bude brát dva argumenty.\n3. Funkce vrátí součet a + b.\n\nEthical Review Feedback: Plan seems to be in alignment with core principles (keyword check). (Decision: approve)"
        else:
            response_content = "Thought: The user wants a plan.\nFinal Answer:\nToto je jednoduchý plán:\n1. Definuj funkci `add(a, b)`.\n2. Funkce bude brát dva argumenty.\n3. Funkce vrátí součet a + b."
    else:
        response_content = "General mock response."

    return ModelResponse(
        id="chatcmpl-mock-123",
        choices=[Choices(finish_reason="stop", index=0, message=Message(content=response_content, role="assistant"))],
        model="mock-model",
        object="chat.completion"
    )

class MockGeminiLLMAdapter(LLM):
    """
    A mock LLM adapter for testing. It is compatible with LangChain and crewAI.
    Its primary role is to act as a placeholder type for the test environment.
    The actual mocking of LLM calls is handled by a monkeypatch.
    """
    model_name: str = "mock-gemini-for-crewai"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        This method should not be called directly in the context of crewAI,
        as the actual calls are intercepted by the monkeypatch.
        """
        raise NotImplementedError(
            "This mock adapter is not meant to be called directly. "
            "The mocking is handled by monkeypatching `litellm.completion`."
        )

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "mock_gemini_llm_adapter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {"model_name": self.model_name}
