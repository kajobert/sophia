import re
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

# Define the input schema for the tool
class DocumentationCheckInput(BaseModel):
    """Input schema for DocumentationCheckTool."""
    diff_content: str = Field(..., description="The git diff content to be analyzed.")

class DocumentationCheckTool(BaseTool):
    name: str = "Documentation Check Tool"
    description: str = "Analyzes a git diff to ensure code changes are documented in WORKLOG.md."
    args_schema: Type[BaseModel] = DocumentationCheckInput

    def _run(self, diff_content: str) -> str:
        """
        The core logic of the tool.
        Analyzes a git diff to ensure documentation is updated alongside code.
        """
        # Use regex to robustly check for a .py file in the '+++' line of the diff.
        has_py_changes = bool(re.search(r"\+\+\+\s.*\.py", diff_content))
        has_worklog_changes = "WORKLOG.md" in diff_content

        if has_py_changes and not has_worklog_changes:
            return "FAIL: The WORKLOG.md was not updated alongside code changes."
        else:
            return "PASS"

# Note: The ReviewerAgentWrapper has been removed as this tool will be called directly.
# This architectural decision was made because the crewai agent framework is not
# well-suited for purely deterministic tasks that do not require an LLM.
# The tool's logic is now encapsulated here and called from a simple script.
