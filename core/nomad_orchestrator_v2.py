"""
Nomad Orchestrator V2 - Proactive State Machine Core.

This refactored version implements a simple, powerful state machine
that replaces the complex, multi-layered architecture. The core idea is
to have a single, intelligent loop that constantly thinks about the next
best action, rather than following a rigid, pre-defined plan.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import json
import re
from enum import Enum

from core.state_manager import StateManager
from core.recovery_manager import RecoveryManager
from core.budget_tracker import BudgetTracker
from core.llm_manager import LLMManager
from core.mcp_client import MCPClient
from core.rich_printer import RichPrinter

class MissionState(Enum):
    """The states of the proactive state machine."""
    THINKING = "THINKING"
    EXECUTING_TOOL = "EXECUTING_TOOL"
    HANDLING_ERROR = "HANDLING_ERROR"
    MISSION_COMPLETE = "MISSION_COMPLETE"

class NomadOrchestratorV2:
    """
    A proactive, state-driven orchestrator.
    
    ARCHITECTURE:
    - A simple, continuous loop: THINKING -> EXECUTING_TOOL -> THINKING...
    - Error handling is a dedicated state: -> HANDLING_ERROR -> EXECUTING_TOOL
    - No more rigid, pre-planned steps. The agent decides the next best action at every step.
    - Context is maintained through a simple history of actions and results.
    """
    
    def __init__(
        self,
        project_root: str = ".",
        session_id: Optional[str] = None,
        max_tokens: int = 100000,
        max_time_seconds: int = 3600,
        max_iterations: int = 50
    ):
        """
        Initializes the proactive NomadOrchestratorV2.
        
        Args:
            project_root: The root directory of the project.
            session_id: The ID of the session to resume or start.
            max_tokens: The maximum number of tokens for the mission.
            max_time_seconds: The maximum duration for the mission.
            max_iterations: A safeguard against infinite loops.
        """
        self.project_root = project_root
        self.max_iterations = max_iterations
        
        # Core components
        self.state_manager = StateManager(project_root, session_id)
        self.recovery_manager = RecoveryManager(project_root)
        self.llm_manager = LLMManager(project_root)
        self.budget_tracker = BudgetTracker(
            max_tokens=max_tokens,
            max_time_seconds=max_time_seconds
        )
        self.mcp_client = MCPClient(project_root)

        # Mission-specific data
        self.mission_goal: str = ""
        self.history: List[Dict[str, Any]] = []
        self.current_state: MissionState = MissionState.THINKING
    
    async def initialize(self) -> None:
        """Initializes all components."""
        await self.mcp_client.start_servers()
        RichPrinter.info("✅ Proactive NomadOrchestratorV2 initialized")
    
    async def execute_mission(
        self,
        mission_goal: str,
        initial_context: Optional[str] = None
    ) -> None:
        """
        The main entry point for starting and running a mission.
        
        This method contains the core state machine loop.

        Args:
            mission_goal: The ultimate objective of the mission.
            initial_context: Optional starting context, e.g., an error log for a recovery mission.
        """
        RichPrinter.info(f"🚀 Starting proactive mission: {mission_goal}")
        self.mission_goal = mission_goal
        self.current_state = MissionState.THINKING
        
        if initial_context:
            self.history.append({"role": "system", "content": f"Initial context for the mission:\n{initial_context}"})

        iteration = 0
        while self.current_state != MissionState.MISSION_COMPLETE:
            if iteration >= self.max_iterations:
                RichPrinter.error("❌ Maximum iterations reached. Mission aborted.")
                break
            
            iteration += 1
            RichPrinter.info(f"--- Iteration {iteration} | State: {self.current_state.value} ---")

            if self.current_state == MissionState.THINKING:
                await self._state_thinking()
            elif self.current_state == MissionState.EXECUTING_TOOL:
                await self._state_executing_tool()
            elif self.current_state == MissionState.HANDLING_ERROR:
                await self._state_handling_error()
            
            await asyncio.sleep(0.1) # Small delay for cleaner logs

        RichPrinter.show_task_complete("Mission has concluded.")
        RichPrinter.info(self.budget_tracker.get_summary())

    # ==================== STATE HANDLERS ====================
    
    async def _state_thinking(self) -> None:
        """
        STATE: THINKING - Decide the next best action.
        
        Actions:
        1. Build a prompt with the mission goal, history, and available tools.
        2. Call the LLM to get the next action (a tool call or `mission_complete`).
        3. Transition to EXECUTING_TOOL or MISSION_COMPLETE.
        """
        prompt = self._build_prompt()
        RichPrinter.info("[THINKING] Building prompt and querying LLM for next action...")

        try:
            model = self.llm_manager.get_llm("powerful")
            response, usage = await model.generate_content_async(prompt)
            
            self.budget_tracker.record_step_cost(f"thinking-{len(self.history)}", usage.get("usage", {}).get("total_tokens", 0), 0)

            parsed_response = self._parse_llm_response(response)
        except Exception as e:
            if "429" in str(e): # Check for rate limit error
                RichPrinter.warning("⚠️ Primary model failed with 429 error. Switching to fallback model.")
                try:
                    model = self.llm_manager.get_llm("fallback")
                    response, usage = await model.generate_content_async(prompt)
                    self.budget_tracker.record_step_cost(f"thinking-fallback-{len(self.history)}", usage.get("usage", {}).get("total_tokens", 0), 0)
                    parsed_response = self._parse_llm_response(response)
                except Exception as fallback_e:
                    RichPrinter.error(f"💥 Fallback model also failed: {fallback_e}")
                    self.history.append({"role": "system", "content": f"Critical error in THINKING state (fallback): {fallback_e}"})
                    self.current_state = MissionState.HANDLING_ERROR
                    return
            else:
                RichPrinter.error(f"💥 Error during thinking phase: {e}")
                self.history.append({"role": "system", "content": f"Critical error in THINKING state: {e}"})
                self.current_state = MissionState.HANDLING_ERROR
                return

        RichPrinter.info("[ACTION PROPOSED] LLM proposed the following action:")
        RichPrinter.agent_tool_code(json.dumps(parsed_response, indent=2))

        if parsed_response.get("tool_name") == "mission_complete":
            RichPrinter.info("✅ LLM decided the mission is complete.")
            self.history.append({"role": "assistant", "content": json.dumps(parsed_response, indent=2)})
            self.current_state = MissionState.MISSION_COMPLETE
        elif "tool_name" in parsed_response:
            self.history.append({"role": "assistant", "content": json.dumps(parsed_response, indent=2)})
            self.current_state = MissionState.EXECUTING_TOOL
        else:
            # The LLM responded without a valid tool call. Treat as an error.
            RichPrinter.warning("⚠️ LLM response did not contain a valid tool call or mission_complete.")
            self.history.append({"role": "system", "content": f"Error: The LLM's response was not a valid tool call. Response: {response}"})
            self.current_state = MissionState.HANDLING_ERROR

    async def _state_executing_tool(self) -> None:
        """
        STATE: EXECUTING_TOOL - Run the chosen tool.
        
        Actions:
        1. Extract the tool call from the last history entry.
        2. Execute the tool via MCPClient.
        3. On success, append result to history and transition to THINKING.
        4. On failure, append error to history and transition to HANDLING_ERROR.
        """
        tool_call_entry = self.history[-1]["content"]
        tool_call = json.loads(tool_call_entry)
        tool_name = tool_call.get("tool_name")
        
        RichPrinter.info(f"[EXECUTING TOOL] Running '{tool_name}'")

        try:
            result = await self.mcp_client.execute_tool(
                tool_name,
                tool_call.get("args", []),
                tool_call.get("kwargs", {}),
                verbose=False # Set to False to avoid duplicate logging from MCP
            )
            
            RichPrinter.info(f"[TOOL RESULT] Tool '{tool_name}' executed successfully.")
            RichPrinter.agent_tool_output(str(result))
            self.history.append({"role": "tool", "content": str(result)})
            self.current_state = MissionState.THINKING

        except Exception as e:
            RichPrinter.error(f"[TOOL RESULT] Tool '{tool_name}' failed.")
            RichPrinter.agent_tool_output(str(e))
            error_message = f"Error executing tool {tool_name}: {e}"
            self.history.append({"role": "tool", "content": error_message})
            self.current_state = MissionState.HANDLING_ERROR

    async def _state_handling_error(self) -> None:
        """
        STATE: HANDLING_ERROR - Decide how to recover from an error.
        
        Actions:
        1. Build a prompt that explicitly includes the last error.
        2. Ask the LLM for a corrective action (a new tool call).
        3. Transition back to EXECUTING_TOOL with the new tool call.
        """
        RichPrinter.warning("🔧 Handling error...")
        prompt = self._build_prompt(is_error_state=True)
        
        try:
            model = self.llm_manager.get_llm("powerful")
            response, usage = await model.generate_content_async(prompt)

            self.budget_tracker.record_step_cost(f"error-handling-{len(self.history)}", usage.get("usage", {}).get("total_tokens", 0), 0)
            parsed_response = self._parse_llm_response(response)
        except Exception as e:
            if "429" in str(e):
                RichPrinter.warning("⚠️ Primary model failed with 429 error during error handling. Switching to fallback model.")
                try:
                    model = self.llm_manager.get_llm("fallback")
                    response, usage = await model.generate_content_async(prompt)
                    self.budget_tracker.record_step_cost(f"error-handling-fallback-{len(self.history)}", usage.get("usage", {}).get("total_tokens", 0), 0)
                    parsed_response = self._parse_llm_response(response)
                except Exception as fallback_e:
                    RichPrinter.error(f"💥 Fallback model also failed during error handling: {fallback_e}")
                    self.history.append({"role": "system", "content": f"Critical error in HANDLING_ERROR state (fallback): {fallback_e}"})
                    # Stay in error state
                    return
            else:
                 RichPrinter.error(f"💥 Critical error during error handling: {e}")
                 self.history.append({"role": "system", "content": f"Critical error in HANDLING_ERROR state: {e}"})
                 # Stay in error state
                 return

        if "tool_name" in parsed_response:
            RichPrinter.info(f"💡 Received corrective action: {parsed_response['tool_name']}")
            self.history.append({"role": "assistant", "content": json.dumps(parsed_response, indent=2)})
            self.current_state = MissionState.EXECUTING_TOOL
        else:
            # The LLM failed to provide a corrective tool call. This is a deeper problem.
            # We'll stay in the error state and add more context for the next attempt.
            RichPrinter.error("❌ LLM failed to provide a corrective action. Retrying.")
            self.history.append({"role": "system", "content": f"Critical Error: The LLM did not provide a corrective tool call after an error. LLM Response: {response}"})
            # The loop will bring us back here, but with more context in the history.

    # ==================== HELPER METHODS ====================
    
    def _build_prompt(self, is_error_state: bool = False) -> str:
        """
        Builds the prompt for the LLM based on the current mission state and history.

        Args:
            is_error_state: If True, the prompt will explicitly ask for a corrective action.
        
        Returns:
            The complete prompt string for the LLM.
        """
        # This should be replaced with a more robust tool listing mechanism in the future.
        available_tools = """
- `list_files(path: str = ".")`: Lists files in a directory.
- `read_file(filepath: str)`: Reads the content of a file.
- `create_file_with_block(filepath: str, content: str)`: Creates a new file with content.
- `replace_with_git_merge_diff(...)`: Performs a targeted search-and-replace in a file.
- `run_in_bash_session(command: str)`: Executes a bash command.
- `create_new_tool(...)`: Creates a new tool for the agent.
- `reload_tools()`: Reloads the available tools.
- `git_tools.*`: Various git operations.
- `mission_complete()`: Call this when the mission goal is achieved.
"""

        history_str = "\n".join([f"**{item['role'].upper()}**:\n{item['content']}" for item in self.history])

        if is_error_state:
            instruction = "The previous step failed. Analyze the error in the last tool response and decide the best next step to fix the problem and continue the mission. What is the next tool call?"
        else:
            instruction = "Analyze the mission goal and the history. What is the single best next step (as a tool call) to achieve the goal? You must complete all parts of the mission goal, especially cleanup steps, before calling `mission_complete`."

        return f"""
You are Nomad, an autonomous AI software engineer. Your goal is to solve the user's request by calling tools.

**MISSION GOAL:** {self.mission_goal}

**AVAILABLE TOOLS:**
{available_tools}

**MISSION HISTORY:**
{history_str}

**INSTRUCTION:**
{instruction}

You must respond with a single JSON object representing the tool call you want to make. Do not add any other text.
Example format:
{{
  "tool_name": "read_file",
  "kwargs": {{
    "filepath": "src/main.py"
  }}
}}
"""

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """
        Parses the JSON tool call from the LLM's response.
        
        Args:
            llm_response: The raw response string from the LLM.
        
        Returns:
            A dictionary representing the tool call, or an empty dict if parsing fails.
        """
        try:
            # Find the first '{' and the last '}' to extract the JSON object
            match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            return {}
        except json.JSONDecodeError:
            RichPrinter.warning(f"⚠️ Could not parse JSON from LLM response: {llm_response}")
            return {}
    
    async def cleanup(self) -> None:
        """Cleans up resources, like shutting down MCP servers."""
        await self.mcp_client.shutdown()
        RichPrinter.info("👋 Proactive NomadOrchestratorV2 shut down.")
