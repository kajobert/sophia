import logging
import json
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class Planner(BasePlugin):
    """A cognitive plugin that creates a plan based on user input."""

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
        plugins = config.get("plugins", {})
        self.llm_tool = plugins.get("tool_llm")
        if not self.llm_tool:
            logger.error("Planner plugin requires 'tool_llm' to be available.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan by instructing the LLM to call a
        predefined function.
        """
        if not context.user_input or not self.llm_tool:
            return context

        tool_description = (
            "Creates a multi-step plan to fulfill the user's request. "
            "Available tools: 'tool_file_system', 'tool_bash', 'tool_git', "
            "'tool_web_search', 'cognitive_code_reader', 'cognitive_doc_reader', "
            "'cognitive_dependency_analyzer', 'cognitive_historian'."
        )

        planner_tool = [
            {
                "type": "function",
                "function": {
                    "name": "create_plan",
                    "description": tool_description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plan": {
                                "type": "array",
                                "description": "An array of tool call objects.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "tool_name": {"type": "string"},
                                        "method_name": {"type": "string"},
                                        "arguments": {"type": "object"},
                                    },
                                    "required": [
                                        "tool_name",
                                        "method_name",
                                        "arguments",
                                    ],
                                },
                            }
                        },
                        "required": ["plan"],
                    },
                },
            }
        ]

        prompt = f"User Request: {context.user_input}"
        planning_context = SharedContext(
            session_id=context.session_id,
            current_state="PLANNING",
            logger=context.logger,
            user_input=prompt,
            history=[{"role": "user", "content": prompt}],
        )

        planned_context = await self.llm_tool.execute(
            planning_context, tools=planner_tool, tool_choice="required"
        )
        llm_message = planned_context.payload.get("llm_response")
        logger.info(f"Raw LLM response received in planner: {llm_message}")

        try:
            tool_calls = llm_message.tool_calls
            if tool_calls:
                plan_str = tool_calls[0].function.arguments
                plan_data = json.loads(plan_str)
                plan = plan_data.get("plan", [])
                context.payload["plan"] = plan
                logger.info(f"Generated plan with {len(plan)} steps via function call.")
            else:
                raise ValueError("LLM did not return a tool call.")

        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.error(
                "Failed to decode plan from LLM response: %s\nResponse was: %s",
                e,
                llm_message,
                exc_info=True,
            )
            context.payload["plan"] = []

        return context
