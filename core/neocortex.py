import os
import importlib
import inspect
import logging

from agents.planner_agent import PlannerAgent
from tools.base_tool import BaseTool
from services.websocket_manager import manager
from .cognitive_layers import ReptilianBrain, MammalianBrain
from .memory_systems import ShortTermMemory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Neocortex:
    """
    The highest level of the cognitive architecture, responsible for executive functions,
    planning, and conscious thought. It orchestrates the lower brain layers and tool execution.
    """

    MAX_REPAIR_ATTEMPTS = 3

    def __init__(
        self,
        reptilian_brain: ReptilianBrain,
        mammalian_brain: MammalianBrain,
        short_term_memory: ShortTermMemory,
        planner: PlannerAgent,
    ):
        self.logger = logging.getLogger(__name__)
        self.reptilian_brain = reptilian_brain
        self.mammalian_brain = mammalian_brain
        self.stm = short_term_memory
        self.planner = planner
        self.tools = self._load_tools()
        self.logger.info("Neocortex initialized.")

    def _load_tools(self) -> dict:
        """Dynamically loads all tool classes from the 'tools' directory."""
        tools = {}
        tools_dir = "tools"
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"tools.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(cls, BaseTool)
                            and cls is not BaseTool
                            and not inspect.isabstract(cls)
                        ):
                            tools[name] = cls()
                except Exception as e:
                    self.logger.error(
                        f"Failed to load or instantiate tool from {module_name}: {e}"
                    )
        return tools

    async def process_input(self, session_id: str, user_input: str):
        """
        The main entry point for processing a new user request.
        It runs the input through the cognitive layers and starts the execution loop.
        """
        self.logger.info(
            f"Neocortex processing new input for session {session_id}: '{user_input}'"
        )

        # 1. Reptilian Brain Processing
        try:
            reptilian_data = self.reptilian_brain.process_input(user_input)
        except ValueError as e:
            self.logger.error(f"Input blocked by ReptilianBrain: {e}")
            await manager.broadcast({"type": "error", "message": str(e)}, session_id)
            return

        # 2. Mammalian Brain Processing
        mammalian_data = self.mammalian_brain.process_input(reptilian_data)

        # 3. Create initial plan
        # The planner now receives a richer context
        # For now, we'll keep it simple and just use the original prompt
        from core.context import SharedContext

        planning_context = SharedContext(
            original_prompt=user_input, session_id=session_id
        )
        planned_context = self.planner.run_task(planning_context)
        initial_plan = planned_context.payload.get("plan")

        if not initial_plan:
            self.logger.error("Planner failed to generate an initial plan.")
            await manager.broadcast(
                {"type": "error", "message": "Could not generate a plan."}, session_id
            )
            return

        # 4. Save initial state and start execution loop
        initial_state = {
            "session_id": session_id,
            "original_prompt": user_input,
            "mammalian_data": mammalian_data,
            "current_plan": initial_plan,
            "step_history": [],
            "repair_attempts": 0,
        }
        self.stm.save_state(session_id, initial_state)
        await self._execute_plan_loop(session_id)

    async def _execute_plan_loop(self, session_id: str):
        """
        The core loop that executes a plan, step by step, handling failures and repairs.
        """
        state = self.stm.load_state(session_id)
        if not state:
            self.logger.error(
                f"No state found for session {session_id}. Aborting execution."
            )
            return

        while state["repair_attempts"] < self.MAX_REPAIR_ATTEMPTS:
            plan_successful = True

            # Create a copy of the plan to iterate over, as the original might be replaced during repair
            plan_to_execute = list(state["current_plan"])

            for step in plan_to_execute:
                try:
                    tool_name = step.get("tool_name")
                    parameters = step.get("parameters", {})
                    if tool_name not in self.tools:
                        raise ValueError(f"Tool '{tool_name}' not found.")

                    tool_instance = self.tools[tool_name]
                    self.logger.info(
                        f"Executing step {step.get('step_id')}: {step.get('description')}"
                    )
                    result = tool_instance.execute(**parameters)

                    step_output = {"status": "success", "result": result}
                    state["step_history"].append({**step, "output": step_output})
                    await manager.broadcast(
                        {
                            "type": "step_update",
                            "step_id": step.get("step_id"),
                            "output": step_output,
                        },
                        session_id,
                    )

                except Exception as e:
                    self.logger.error(f"Step {step.get('step_id')} failed: {e}")
                    plan_successful = False
                    step_output = {"status": "error", "error": str(e)}
                    state["step_history"].append({**step, "output": step_output})
                    await manager.broadcast(
                        {
                            "type": "step_update",
                            "step_id": step.get("step_id"),
                            "output": step_output,
                        },
                        session_id,
                    )

                    # --- Repair Loop ---
                    state["repair_attempts"] += 1
                    if state["repair_attempts"] >= self.MAX_REPAIR_ATTEMPTS:
                        self.logger.error(
                            f"Max repair attempts reached for session {session_id}."
                        )
                        await manager.broadcast(
                            {
                                "type": "plan_failed",
                                "message": "Max repair attempts reached.",
                            },
                            session_id,
                        )
                        break

                    self.logger.info("Calling PlannerAgent to repair the plan...")
                    from core.context import SharedContext

                    repair_prompt = f"The previous plan failed. Original goal: {state['original_prompt']}. Failed plan: {state['current_plan']}. The step '{step.get('description')}' failed with the error: {str(e)}. Please create a new plan."
                    repair_context = SharedContext(
                        original_prompt=repair_prompt, session_id=session_id
                    )
                    repaired_context = self.planner.run_task(repair_context)
                    new_plan = repaired_context.payload.get("plan")

                    if new_plan:
                        self.logger.info(
                            "Received a new plan. Restarting execution loop."
                        )
                        state["current_plan"] = new_plan
                        state["step_history"] = []  # Reset history for the new plan
                        await manager.broadcast(
                            {"type": "plan_repaired", "new_plan": new_plan}, session_id
                        )
                        # Break the inner for-loop to restart the while-loop with the new plan
                        break
                    else:
                        self.logger.error(
                            "Planner failed to provide a new plan. Aborting."
                        )
                        await manager.broadcast(
                            {
                                "type": "plan_failed",
                                "message": "Planner failed to repair the plan.",
                            },
                            session_id,
                        )
                        # Set attempts to max to exit the while loop
                        state["repair_attempts"] = self.MAX_REPAIR_ATTEMPTS
                        break

            # Save state after each step or failure
            self.stm.save_state(session_id, state)

            if (
                not plan_successful
                and state["repair_attempts"] < self.MAX_REPAIR_ATTEMPTS
            ):
                # This continue is important to restart the while loop with the new plan
                continue

            if plan_successful:
                self.logger.info(
                    f"Plan for session {session_id} executed successfully."
                )
                await manager.broadcast(
                    {"type": "plan_success", "message": "Plan executed successfully."},
                    session_id,
                )
                break

        # Final state save
        self.stm.save_state(session_id, state)
