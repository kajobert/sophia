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
        self.prompt_template = ""
        try:
            with open("config/prompts/planner_prompt_template.txt", "r") as f:
                self.prompt_template = f.read()
        except FileNotFoundError:
            logger.error("Planner prompt template not found. The planner will not be effective.")
            self.prompt_template = "Create a plan. Available tools: {tool_list}"

        self.plugins = config.get("plugins", {})
        self.llm_tool = self.plugins.get("tool_llm")
        if not self.llm_tool:
            logger.error("Planner plugin requires 'tool_llm' to be available.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan by instructing the LLM to call a
        predefined function.
        """
        if not context.user_input or not self.llm_tool:
            return context

        # --- Dynamically discover available tools ---
        available_tools = []
        for plugin in self.plugins.values():
            if hasattr(plugin, "get_tool_definitions"):
                for tool_def in plugin.get_tool_definitions():
                    # We only need the function name and description for the planner's prompt
                    func = tool_def.get("function", {})
                    if "name" in func and "description" in func:
                        tool_string = f"- {plugin.name}.{func['name']}: {func['description']}"
                        available_tools.append(tool_string)

        tool_list_str = "\n".join(available_tools)
        tool_description = self.prompt_template.format(tool_list=tool_list_str)

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
                                        "tool_name": {
                                            "type": "string",
                                            "description": "Name of the tool plugin.",
                                        },
                                        "method_name": {
                                            "type": "string",
                                            "description": "The method to call.",
                                        },
                                        "arguments": {
                                            "type": "object",
                                            "description": "Arguments for the method.",
                                        },
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
        )

        planned_context = await self.llm_tool.execute(
            planning_context, tools=planner_tool, tool_choice="required"
        )
        llm_message = planned_context.payload.get("llm_response")
        # fmt: off
        logger.info(f"Raw LLM response received in planner: {llm_message}")  # noqa: E501
        # fmt: on

        try:
            tool_calls = llm_message.tool_calls
            plan = []

            if not tool_calls:
                logger.info("No tool calls received, creating empty plan.")
            # Scénář 1: Chytrý model vrátil přímo seznam nástrojů
            elif len(tool_calls) > 1 or tool_calls[0].function.name != "create_plan":
                for call in tool_calls:
                    tool_name, method_name = call.function.name.split('.')
                    try:
                        arguments = json.loads(call.function.arguments) if call.function.arguments else {}
                    except json.JSONDecodeError:
                        arguments = {}

                    plan.append({
                        "tool_name": tool_name,
                        "method_name": method_name,
                        "arguments": arguments,
                    })
                logger.info(f"Generated plan with {len(plan)} steps directly from tool calls.")
            # Scénář 2: Starší model vrátil vše zabalené v 'create_plan'
            elif tool_calls[0].function.name == "create_plan":
                plan_str = tool_calls[0].function.arguments
                plan_data = json.loads(plan_str)
                plan = plan_data.get("plan", [])
                logger.info(f"Generated plan with {len(plan)} steps via function call.")

            context.payload["plan"] = plan

        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.error(
                "Failed to decode plan from LLM response: %s\nResponse was: %s",
                e,
                llm_message,
                exc_info=True,
            )
            context.payload["plan"] = []

        return context
