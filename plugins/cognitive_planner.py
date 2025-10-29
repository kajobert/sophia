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
        context.logger.info(
            f"Raw LLM response received in planner: {llm_message}",
            extra={"plugin_name": self.name},
        )

        try:
            tool_calls = llm_message.tool_calls
            plan = []

            if not tool_calls:
                context.logger.info(
                    "No tool calls received, creating empty plan.",
                    extra={"plugin_name": self.name},
                )
            # Scenario 1: The model returned a direct list of tool calls
            elif len(tool_calls) > 1 or tool_calls[0].function.name != "create_plan":
                for call in tool_calls:
                    try:
                        tool_name, method_name = call.function.name.split(".", 1)
                        # Robustly decode arguments
                        raw_args = call.function.arguments
                        if raw_args and raw_args.strip():
                            try:
                                arguments = json.loads(raw_args)
                            except json.JSONDecodeError:
                                context.logger.warning(
                                    f"JSONDecodeError for arguments: '{raw_args}'. Defaulting to empty dict.",
                                    extra={"plugin_name": self.name},
                                )
                                arguments = {}
                        else:
                            arguments = {}

                        plan.append(
                            {
                                "tool_name": tool_name,
                                "method_name": method_name,
                                "arguments": arguments,
                            }
                        )
                    except ValueError:
                        context.logger.error(
                            f"Invalid tool call format: {call.function.name}. Expected 'plugin.method'.",
                            extra={"plugin_name": self.name},
                        )
                context.logger.info(
                    f"Generated plan with {len(plan)} steps directly from tool calls.",
                    extra={"plugin_name": self.name},
                )
            # Scenario 2: The model wrapped the plan in a 'create_plan' function call
            elif tool_calls[0].function.name == "create_plan":
                plan_str = tool_calls[0].function.arguments
                plan_data = json.loads(plan_str)
                plan = plan_data.get("plan", [])
                context.logger.info(
                    f"Generated plan with {len(plan)} steps via function call.",
                    extra={"plugin_name": self.name},
                )

            context.payload["plan"] = plan

        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            context.logger.error(
                "Failed to decode plan from LLM response: %s\nResponse was: %s",
                e,
                llm_message,
                exc_info=True,
                extra={"plugin_name": self.name},
            )
            context.payload["plan"] = []

        return context
