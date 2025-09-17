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
        prompt = messages[-1].get("content", "")

    prompt_lower = prompt.lower()

    response_content = ""

    # This condition is designed to catch the "observation" step in crewai.
    # When a tool runs, its output is passed back to the LLM as the next prompt.
    # This mock logic identifies such prompts (based on content from integration tests)
    # and makes the agent's final answer simply be that observation.
    if "this is a readable test file" in prompt_lower or "hello from the integration test" in prompt_lower:
        response_content = f"Thought: The tool has been executed and I have the result. I will now formulate the final answer based on the tool's output.\nFinal Answer: {prompt}"
    elif "analyzuj tento požadavek" in prompt_lower and "ethical review tool" in prompt_lower:
        response_content = "Thought: The user wants a plan and an ethical review. I will create the plan and then use the Ethical Review Tool.\nFinal Answer:Here is the plan: A simple test plan for the user request.\n\nEthical Review Feedback: The plan is ethically sound."
    elif "na základě tohoto plánu vytvoř kód" in prompt_lower:
        response_content = "Thought: The user wants code based on the plan. I will provide a Python code block.\nFinal Answer:\n```python\ndef add(a, b):\n  # This function adds two numbers\n  return a + b\n```"
    elif "otestuj tento kód" in prompt_lower:
        response_content = "Thought: The user wants me to test the code. I will confirm it's functional.\nFinal Answer: Kód je funkční a splňuje všechny požadavky."
    # This mock is for the EngineerAgent trying to use the WriteFileTool.
    # It's designed to be flexible enough to handle various phrasings.
    elif "write a file" in prompt_lower or "create a file named" in prompt_lower:
        import re
        # Regex to find file path and content, tolerant of different phrasings and case-insensitive.
        path_match = re.search(r"file\s+(?:to|named)\s+'([^']*)'", prompt, re.IGNORECASE)
        content_match = re.search(r"(?:with\s+)?content:?\s+'([^']*)'", prompt, re.IGNORECASE)

        if path_match and content_match:
            file_path = path_match.group(1)
            content = content_match.group(1)

            # This is the structured output crewAI expects for a tool call.
            response_content = (
                "Thought: The user wants me to write a file. I will use the 'Write File' tool.\n"
                f"Action: Write File\n"
                f"Action Input: {{\"file_path\": \"{file_path}\", \"content\": \"{content}\"}}"
            )
        else:
            # Fallback for the generic "create code" prompt if parsing fails
            response_content = "Thought: The user wants code based on the plan. I will provide a Python code block.\nFinal Answer:\n```python\ndef add(a, b):\n  # This function adds two numbers\n  return a + b\n```"

    elif "use the read file tool to read the file" in prompt_lower:
        import re
        path_match = re.search(r"named '(.*?)'", prompt)
        if path_match:
            file_path = path_match.group(1)
            response_content = (
                "Thought: The user wants me to read a file. I will use the 'Read File' tool.\n"
                f"Action: Read File\n"
                f"Action Input: {{\"file_path\": \"{file_path}\"}}"
            )
        else:
            response_content = "Thought: I was asked to read a file for the integration test, but I couldn't parse the file path from the prompt."
    else:
        response_content = "Thought: The user wants a plan and an ethical review. I will create the plan and then use the Ethical Review Tool.\nFinal Answer:Here is the plan: A simple test plan for the user request.\n\nAnd here is the ethical review: The plan is ethically sound."

    return ModelResponse(
        id="chatcmpl-mock-123",
        choices=[Choices(finish_reason="stop", index=0, message=Message(content=response_content, role="assistant"))],
        model="mock-model",
        object="chat.completion"
    )

class MockGeminiLLMAdapter(LLM):
    """
    A mock LLM adapter for testing. It is compatible with LangChain and crewAI.
    """
    model_name: str

    def __init__(self, model: str = "mock-gemini-for-crewai", **kwargs: Any):
        # Pass the model_name to the Pydantic model's __init__
        super().__init__(model_name=model, **kwargs)

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        raise NotImplementedError(
            "This mock adapter is not meant to be called directly. "
            "The mocking is handled by monkeypatching `litellm.completion`."
        )

    @property
    def _llm_type(self) -> str:
        return "mock_gemini_llm_adapter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}
