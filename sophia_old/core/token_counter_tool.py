import tiktoken
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class TokenCounterToolSchema(BaseModel):
    text: str = Field(..., description="The text to count tokens for.")


class TokenCounterTool(BaseTool):
    """A tool to count the number of tokens in a given text."""

    name: str = "TokenCounterTool"
    description: str = (
        "Counts the number of tokens in a given text using the 'cl100k_base' encoding."
    )
    args_schema: type[BaseModel] = TokenCounterToolSchema

    def _run(self, text: str) -> int:
        """Counts the tokens in the provided text."""
        if not isinstance(text, str):
            return "Error: Input must be a string."

        try:
            # This encoding is widely used by OpenAI models.
            encoding = tiktoken.get_encoding("cl100k_base")
            num_tokens = len(encoding.encode(text))
            return num_tokens
        except Exception as e:
            return f"Error counting tokens: {e}"
