import json
from typing import Any, List, Optional, Dict
from langchain_core.language_models.llms import LLM

class MockGeminiLLMAdapter(LLM):
    """
    A mock of the GeminiLLMAdapter that is compatible with LangChain.
    It returns a canned response to force a tool call in tests.
    """

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """
        Mocks the LLM call. Returns a formatted string that instructs
        a crewAI agent to use the 'Write File' tool.
        """
        tool_call = {
            "tool_name": "Write File",
            "arguments": {
                "file_path": "test_output.py",
                "content": "print('This is a test file created by the engineer.')"
            }
        }

        response_string = f"""
Thought: The user wants me to create the file 'test_output.py'. I will use the 'Write File' tool to do this.
Action:
```json
{json.dumps(tool_call)}
```
"""
        return response_string

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "mock_gemini_llm_adapter"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {"model_name": "mock"}
