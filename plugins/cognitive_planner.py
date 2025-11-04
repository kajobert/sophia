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
        offline_mode = config.get("offline_mode", False)
        
        # Use simplified prompt in offline mode (smaller context for 8B models)
        prompt_file = "config/prompts/planner_offline_prompt.txt" if offline_mode else "config/prompts/planner_prompt_template.txt"
        
        try:
            with open(prompt_file, "r") as f:
                self.prompt_template = f.read()
            if offline_mode:
                logger.info("Using simplified offline planner prompt")
        except FileNotFoundError:
            logger.error(
                f"Planner prompt template not found: {prompt_file}",
                extra={"plugin_name": "cognitive_planner"},
            )
            self.prompt_template = "Create a plan. Available tools: {tool_list}"

        self.plugins = config.get("all_plugins", {})
        # Use local LLM in offline mode, cloud LLM otherwise
        offline_mode = config.get("offline_mode", False)
        if offline_mode:
            self.llm_tool = self.plugins.get("tool_local_llm")
            if self.llm_tool:
                logger.info("Planner using tool_local_llm (offline mode)")
        else:
            self.llm_tool = self.plugins.get("tool_llm")
            if self.llm_tool:
                logger.info("Planner using tool_llm (cloud mode)")
        
        if not self.llm_tool:
            logger.error(
                "Planner plugin requires an LLM tool (tool_local_llm or tool_llm) to be available.",
                extra={"plugin_name": "cognitive_planner"},
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan by instructing the LLM to call a
        predefined function. It can handle both a single 'create_plan' call
        and properly extract multiple tool calls from the response.
        
        Respects offline_mode from context to select appropriate LLM.
        """
        # Select LLM based on offline mode (runtime decision)
        if context.offline_mode:
            # Force local LLM in offline mode
            llm_tool = self.plugins.get("tool_local_llm")
            if not llm_tool:
                context.logger.error(
                    "Offline mode enabled but tool_local_llm not available!",
                    extra={"plugin_name": "cognitive_planner"}
                )
                context.payload["plan"] = []
                return context
            context.logger.info(
                "🔒 Planner using local LLM (offline mode)",
                extra={"plugin_name": "cognitive_planner"}
            )
        else:
            # Use configured LLM (cloud for stability)
            llm_tool = self.llm_tool
            context.logger.debug(
                "☁️ Planner using cloud LLM (online mode)",
                extra={"plugin_name": "cognitive_planner"}
            )
        
        if not context.user_input or not llm_tool:
            return context

        # --- Dynamically discover available tools ---
        available_tools = []
        
        # In offline mode, only include essential tools to reduce prompt size
        if context.offline_mode:
            essential_tool_names = {
                "tool_local_llm",  # LLM execution
                "tool_code_workspace",  # Read project files
                "tool_file_system",  # Read/write sandbox files
                "tool_datetime",  # Time queries
                "tool_terminal",  # Terminal commands
            }
        else:
            essential_tool_names = None  # Include all tools in online mode
        
        for plugin in self.plugins.values():
            # Skip if not in essential set (when in offline mode)
            if essential_tool_names and plugin.name not in essential_tool_names:
                continue
            
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

        # Use the selected LLM tool (respects offline mode)
        planned_context = await llm_tool.execute(context=planning_context)
        llm_message = planned_context.payload.get("llm_response")
        context.logger.info(
            f"Raw LLM response received in planner: {llm_message}",
            extra={"plugin_name": "cognitive_planner"},
        )

        try:
            # --- Robust Plan Extraction (Handles multiple response formats) ---
            plan_data = []
            if isinstance(llm_message, list) and hasattr(llm_message[0], "function"):
                # Handle direct tool_calls format (e.g., from claude-3.5-sonnet, Ollama)
                tool_call = llm_message[0]
                if tool_call.function.name == "create_plan":
                    arguments = tool_call.function.arguments
                    
                    # Handle both string JSON and dict (Ollama returns dict, OpenAI returns string)
                    if isinstance(arguments, dict):
                        # Ollama format: arguments is already a dict
                        plan_str = arguments.get("plan", "[]")
                        # Plan can be string JSON or already parsed
                        if isinstance(plan_str, str):
                            # Tolerant parsing for incomplete JSON (8B models may truncate)
                            if plan_str and not plan_str.strip().endswith("]"):
                                logger.warning(f"⚠️ Incomplete JSON: {plan_str[:80]}...")
                                if plan_str.count("[") > plan_str.count("]"):
                                    plan_str = plan_str.rstrip() + "}]"
                                    logger.info("✅ Auto-fixed incomplete JSON")
                            plan_data = json.loads(plan_str)
                        else:
                            plan_data = plan_str  # Already a list
                    else:
                        # OpenAI format: arguments is JSON string
                        plan_data = json.loads(arguments).get("plan", [])
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
