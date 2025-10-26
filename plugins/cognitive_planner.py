import logging
from typing import List, Dict, Any
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import json

logger = logging.getLogger(__name__)

class Planner(BasePlugin):
    """A cognitive plugin that creates a plan (a sequence of tool calls) based on user input."""
    
    # SECURITY: Dangerous patterns that indicate potential attacks in plans
    DANGEROUS_COMMAND_PATTERNS = [
        "rm -rf", "dd if=", "mkfs", "> /dev/", "chmod 777",
        "curl", "wget", "nc ", "bash -c", "sh -c",
        "eval", "exec", "import os", "import subprocess",
        "__import__", "compile(", "globals(", "locals(",
    ]
    
    # SECURITY: Dangerous file paths that should never be accessed
    DANGEROUS_PATHS = [
        "/etc/passwd", "/etc/shadow", "~/.ssh", "/root/",
        "../", "../../", "/dev/", "/proc/", "/sys/",
        "core/kernel.py", "core/plugin_manager.py",
        "config/settings.yaml", ".git/config",
    ]

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

    def _validate_plan_safety(self, plan: List[Dict[str, Any]]) -> tuple[bool, str]:
        """
        Validates that a plan does not contain dangerous operations.
        
        SECURITY: This prevents LLM prompt injection attacks by:
        1. Checking for dangerous command patterns
        2. Checking for dangerous file paths
        3. Validating tool/method names are known safe
        
        Args:
            plan: The plan to validate (list of tool call dicts).
            
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        for i, step in enumerate(plan):
            tool_name = step.get("tool_name", "")
            method_name = step.get("method_name", "")
            arguments = step.get("arguments", {})
            
            # 1. Check for dangerous patterns in all string arguments
            for key, value in arguments.items():
                if isinstance(value, str):
                    # Check for dangerous command patterns
                    for pattern in self.DANGEROUS_COMMAND_PATTERNS:
                        if pattern in value.lower():
                            return False, (
                                f"Step {i+1}: Dangerous pattern '{pattern}' detected "
                                f"in argument '{key}': {value}"
                            )
                    
                    # Check for dangerous file paths
                    for path_pattern in self.DANGEROUS_PATHS:
                        if path_pattern in value:
                            return False, (
                                f"Step {i+1}: Dangerous path pattern '{path_pattern}' "
                                f"detected in argument '{key}': {value}"
                            )
            
            # 2. Validate tool names are from known safe set
            safe_tools = {
                "tool_file_system", "tool_bash", "tool_git", "tool_web_search",
                "cognitive_code_reader", "cognitive_doc_reader",
                "cognitive_dependency_analyzer", "cognitive_historian"
            }
            if tool_name not in safe_tools:
                return False, f"Step {i+1}: Unknown or unsafe tool name: {tool_name}"
            
            # 3. Extra validation for bash commands
            if tool_name == "tool_bash" and method_name == "execute_command":
                command = arguments.get("command", "")
                # Additional check for shell metacharacters
                dangerous_chars = ["|", "&&", "||", ";", "`", "$(", ">", "<"]
                for char in dangerous_chars:
                    if char in command:
                        return False, (
                            f"Step {i+1}: Shell metacharacter '{char}' detected "
                            f"in bash command: {command}"
                        )
        
        return True, ""

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Takes user input and generates a plan in the context payload.
        The plan is a JSON array of tool calls.
        
        SECURITY: Plans are validated before being added to context.
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
            
            # SECURITY: Validate the plan before accepting it
            is_safe, reason = self._validate_plan_safety(plan)
            if not is_safe:
                logger.error(f"Plan validation failed: {reason}")
                logger.error(f"Rejected plan: {json.dumps(plan, indent=2)}")
                context.payload["plan"] = []
                context.payload["plan_error"] = f"Security validation failed: {reason}"
                return context
            
            context.payload["plan"] = plan
            logger.info(f"Successfully generated and validated plan with {len(plan)} steps.")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode plan from LLM response: {plan_str}")
            context.payload["plan"] = []
        return context
