import logging
from typing import List, Dict, Any
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import json

logger = logging.getLogger(__name__)

class Planner(BasePlugin):
    """A cognitive plugin that creates a plan (a sequence of tool calls) based on user input."""

    @property
    def name(self) -> str:
        return "cognitive_planner"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """This plugin requires the LLM tool to function."""
        self.llm_tool = config.get("tool_llm")
        if not self.llm_tool:
            logger.error("Planner plugin requires the 'tool_llm' to be available.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan in the context payload.
        The plan is a JSON array of tool calls.
        """
        if not context.user_input or not self.llm_tool:
            return context

        # Create a special prompt for the LLM to generate a plan
        system_prompt = """
You are a planning module. Your task is to take a user request and convert it into a JSON array of tool calls.
Available tools are: 'tool_file_system', 'tool_bash', 'tool_git', 'tool_web_search', 'cognitive_code_reader', 'cognitive_doc_reader', 'cognitive_dependency_analyzer', 'cognitive_historian'.
You must respond ONLY with a valid JSON array. Do not add any other text.
Each object in the array must have "tool_name", "method_name", and "arguments" (as a dictionary).

Example User Request: "Read the file 'hello.txt'"
Example JSON Response:
[
    {
        "tool_name": "tool_file_system",
        "method_name": "read_file",
        "arguments": {
            "path": "hello.txt"
        }
    }
]
"""

        # We create a temporary context for the planning LLM call
        planning_context = SharedContext(
            session_id=context.session_id,
            current_state="PLANNING",
            logger=context.logger,
            user_input=system_prompt + "\nUser Request: " + context.user_input,
            history=[]  # Planning should be context-free for now
        )

        planned_context = await self.llm_tool.execute(planning_context)
        plan_str = planned_context.payload.get("llm_response", "[]")

        try:
            plan = json.loads(plan_str)
            context.payload["plan"] = plan
            logger.info(f"Successfully generated plan with {len(plan)} steps.")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode plan from LLM response: {plan_str}")
            context.payload["plan"] = []
        return context
