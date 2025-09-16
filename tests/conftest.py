import pytest
import os
from litellm.utils import ModelResponse, Choices, Message

def mock_litellm_completion(*args, **kwargs):
    """
    Mocks the litellm.completion function to avoid real LLM calls during tests.
    It inspects the prompt and returns a canned response suitable for the test.
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

    response = ModelResponse(
        id="chatcmpl-mock-123",
        choices=[Choices(finish_reason="stop", index=0, message=Message(content=response_content, role="assistant"))],
        model="mock-model", # This model name doesn't matter as the call is mocked
        object="chat.completion"
    )
    return response

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
    This fixture automatically mocks `litellm.completion` for every test.
    This is the most robust way to prevent real LLM calls and control test outcomes,
    and it works seamlessly with the new LLM factory architecture.
    """
    monkeypatch.setattr("litellm.completion", mock_litellm_completion)
    # Also mock the async version if it's used elsewhere
    monkeypatch.setattr("litellm.acompletion", mock_litellm_completion)
    print("--- `litellm.completion` has been monkeypatched ---")
