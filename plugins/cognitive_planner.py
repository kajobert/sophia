import logging
import json
import re
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
        self.prompt_template = ""
        try:
            with open("config/prompts/planner_prompt_template.txt", "r") as f:
                self.prompt_template = f.read()
        except FileNotFoundError:
            logger.error(
                "Planner prompt template not found. The planner will not be effective.",
                extra={"plugin_name": "cognitive_planner"},
            )
            self.prompt_template = "Create a plan. Available tools: {tool_list}"

        self.plugins = config.get("all_plugins", {})
        self.llm_tool = self.plugins.get("tool_llm")
        if not self.llm_tool:
            logger.error(
                "Planner plugin requires 'tool_llm' to be available.",
                extra={"plugin_name": "cognitive_planner"},
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan by instructing the LLM to call a
        predefined function. It can handle both a single 'create_plan' call
        and a direct list of tool calls from more advanced models.
        """
        if not context.user_input or not self.llm_tool:
            return context

        # --- Dynamically discover available tools ---
        available_tools = []
        for plugin in self.plugins.values():
            # Skip Langfuse temporarily due to validation issues
            if plugin.name == "tool_langfuse":
                continue

            if hasattr(plugin, "get_tool_definitions"):
                for tool_def in plugin.get_tool_definitions():
                    func = tool_def.get("function", {})
                    if "name" in func and "description" in func:
                        # Keep tool_name and method_name separate for clarity
                        tool_string = (
                            f"- tool_name: '{plugin.name}', "
                            f"method_name: '{func['name']}', "
                            f"description: '{func['description']}'"
                        )
                        available_tools.append(tool_string)

        tool_list_str = "\n".join(available_tools)
        tool_description = self.prompt_template.format(
            tool_list=tool_list_str, user_input=context.user_input
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
                                    "required": ["tool_name", "method_name", "arguments"],
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
            payload=context.payload.copy(),  # Propagate payload
        )

        planning_context.payload["tools"] = planner_tool
        planning_context.payload["tool_choice"] = "auto"

        planned_context = await self.llm_tool.execute(context=planning_context)
        llm_message = planned_context.payload.get("llm_response")
        context.logger.info(
            f"Raw LLM response received in planner: {llm_message}",
            extra={"plugin_name": "cognitive_planner"},
        )

        try:
            # --- Robust Plan Extraction (Handles multiple response formats) ---
            plan_data = []
            if isinstance(llm_message, list) and hasattr(llm_message[0], "function"):
                # Handle direct tool_calls format (e.g., from claude-3.5-sonnet)
                tool_call = llm_message[0]
                if tool_call.function.name == "create_plan":
                    plan_str = tool_call.function.arguments
                    plan_data = json.loads(plan_str).get("plan", [])
            else:
                # Handle raw string or object with .content
                response_text = (
                    str(llm_message.content)
                    if hasattr(llm_message, "content")
                    else str(llm_message)
                )
                json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
                if json_match:
                    plan_str = json_match.group(0)
                    plan_data = json.loads(plan_str)

            if not plan_data:
                context.logger.warning(
                    "No valid plan found in LLM response, creating empty plan.",
                    extra={"plugin_name": "cognitive_planner"},
                )
                context.payload["plan"] = []
            else:
                context.payload["plan"] = plan_data

        except (json.JSONDecodeError, AttributeError, ValueError, TypeError) as e:
            context.logger.error(
                "Failed to decode or process plan from LLM response: %s\nResponse was: %s",
                e,
                llm_message,
                exc_info=True,
                extra={"plugin_name": "cognitive_planner"},
            )
            context.payload["plan"] = []

        return context
