import pytest
import os
from litellm.utils import ModelResponse, Choices, Message

def mock_litellm_completion(*args, **kwargs):
    """
    Mocks the litellm.completion function to avoid real LLM calls.
    It inspects the prompt and returns a canned response suitable for the test.
    The order of checks is important.
    """
    messages = kwargs.get("messages", [])
    prompt = ""
    if messages:
        # The relevant prompt is usually the last message in the list
        prompt = messages[-1].get("content", "")

    prompt_lower = prompt.lower()

    response_content = ""
    # Check for the more specific prompt (engineer's) first.
    if "kód" in prompt_lower or "code" in prompt_lower:
        response_content = """
Thought: The user wants code based on the plan. I will provide a Python code block.
Final Answer:
```python
def add(a, b):
  # This function adds two numbers
  return a + b
```
"""
    # Then check for the more general prompt (planner's).
    elif "plán" in prompt_lower or "plan" in prompt_lower:
        response_content = """
Thought: The user wants a plan. I will provide a step-by-step plan.
Final Answer:
Toto je jednoduchý plán:
1. Definuj funkci `add(a, b)`.
2. Funkce bude brát dva argumenty.
3. Funkce vrátí součet a + b.
"""
    else:
        # Fallback for any other unexpected calls
        response_content = "General mock response."

    # Construct a valid litellm.ModelResponse object
    response = ModelResponse(
        id="chatcmpl-mock-123",
        choices=[
            Choices(
                finish_reason="stop",
                index=0,
                message=Message(
                    content=response_content,
                    role="assistant"
                )
            )
        ],
        model="mock-model",
        object="chat.completion"
    )
    return response

def pytest_configure(config):
    """
    This hook runs at the beginning of the test session.
    It sets the environment variable to make the app load `config_test.yaml`.
    """
    os.environ['SOPHIA_ENV'] = 'test'
    print("\n--- SOPHIA_ENV set to 'test' via pytest_configure ---")

@pytest.fixture(scope="function", autouse=True)
def mock_llm_calls(monkeypatch):
    """
    This fixture automatically mocks `litellm.completion` for every test.
    This is the most robust way to prevent real LLM calls and control test outcomes.
    """
    monkeypatch.setattr("litellm.completion", mock_litellm_completion)
    # Also mock the async version if it's used elsewhere
    monkeypatch.setattr("litellm.acompletion", mock_litellm_completion)
