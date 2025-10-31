import logging
import json
import re
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


def extract_json_plan(text: str) -> list | None:
    """Extracts a JSON array of plan steps from a text block."""
    # Regex to find a JSON array within the text
    match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
    if match:
        json_block = match.group(0)
        try:
            return json.loads(json_block)
        except json.JSONDecodeError:
            return None
    return None


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
            self.prompt_template = "Create a plan. Available tools: {tool_list}"

        self.plugins = config.get("plugins", {})
        self.llm_tool = self.plugins.get("tool_llm")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Generates a plan by calling an LLM and robustly parsing its response.
        Handles direct tool calls, wrapped plans, and raw JSON in text.
        """
        if not context.user_input or not self.llm_tool:
            return context

        available_tools = []
        for plugin in self.plugins.values():
            if hasattr(plugin, "get_tool_definitions"):
                for tool_def in plugin.get_tool_definitions():
                    func = tool_def.get("function", {})
                    if "name" in func and "description" in func:
                        available_tools.append(f"- {plugin.name}.{func['name']}: {func['description']}")

        tool_list_str = "\n".join(available_tools)
        tool_description = self.prompt_template.format(tool_list=tool_list_str)

        planner_tool = [{"type": "function", "function": {"name": "create_plan", "description": tool_description, "parameters": {"type": "object", "properties": {"plan": {"type": "array", "items": {"type": "object", "properties": {"tool_name": {"type": "string"}, "method_name": {"type": "string"}, "arguments": {"type": "object"}}, "required": ["tool_name", "method_name", "arguments"]}}}, "required": ["plan"]}}}]

        prompt = f"User Request: {context.user_input}"
        planning_context = SharedContext(session_id=context.session_id, current_state="PLANNING", logger=context.logger, user_input=prompt, history=[{"role": "user", "content": prompt}], payload={"tools": planner_tool, "tool_choice": "auto"})

        planned_context = await self.llm_tool.execute(planning_context)
        llm_message = planned_context.payload.get("llm_response")
        logger.info(f"Raw LLM response in planner: {llm_message}")

        plan = []
        try:
            if hasattr(llm_message, "tool_calls") and llm_message.tool_calls:
                tool_calls = llm_message.tool_calls
                if tool_calls[0].function.name == "create_plan":
                    plan_data = json.loads(tool_calls[0].function.arguments)
                    plan = plan_data.get("plan", [])
                else:
                    for call in tool_calls:
                        tool_name, method_name = call.function.name.split(".", 1)
                        arguments = json.loads(call.function.arguments or "{}")
                        plan.append({"tool_name": tool_name, "method_name": method_name, "arguments": arguments})

            elif llm_message and isinstance(llm_message, str):
                logger.warning(f"LLMTool returned a string, not a message object: {llm_message}")
                plan = []
            elif llm_message and isinstance(llm_message.content, str):
                extracted_plan = extract_json_plan(llm_message.content)
                if extracted_plan:
                    plan = extracted_plan
                    logger.info(f"Successfully extracted JSON plan from text content.")
                else:
                    logger.warning("Could not extract a valid JSON plan from LLM content.")

        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logger.error(f"Failed to parse plan from LLM: {e}", exc_info=True)

        context.payload["plan"] = plan
        return context
