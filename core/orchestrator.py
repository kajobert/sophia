import os
import importlib
import inspect
import logging
import asyncio
from core.context import SharedContext
from agents.planner_agent import PlannerAgent
from tools.base_tool import BaseTool
from web.api.websocket_manager import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Orchestrator:
    """
    Central orchestrator to execute plans, handle failures, and trigger a cognitive cycle for plan correction.
    """

    MAX_REPAIR_ATTEMPTS = 3

    def __init__(self, llm):
        # The LLM is passed to the planner for plan generation and correction.
        self.planner = PlannerAgent(llm)
        self.tools = self._load_tools()

    def _load_tools(self) -> dict:
        """
        Dynamically loads all tool classes from the 'tools' directory that inherit from BaseTool.
        The key is the class name.
        """
        tools = {}
        tools_dir = "tools"
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"tools.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        # Ensure it's a tool, not a base class or other import
                        if issubclass(cls, BaseTool) and cls is not BaseTool and not inspect.isabstract(cls):
                            try:
                                tools[name] = cls()
                                logging.info(f"Successfully loaded tool: {name}")
                            except Exception as e:
                                logging.error(f"Failed to instantiate tool {name}: {e}")
                except Exception as e:
                    logging.error(f"Failed to load module {module_name}: {e}")
        return tools

    async def execute_plan(self, context: SharedContext):
        """
        Executes a plan from the shared context, handling failures and repairs, and broadcasting updates.
        """
        repair_attempts = 0
        while repair_attempts < self.MAX_REPAIR_ATTEMPTS:
            if not context.current_plan or not isinstance(context.current_plan, list):
                logging.error("No valid plan to execute. Aborting.")
                context.feedback = "Execution aborted: No plan provided."
                await manager.broadcast({"type": "plan_feedback", "feedback": context.feedback}, context.session_id)
                return context

            plan_successful = True
            for step in context.current_plan:
                try:
                    tool_name = step.get("tool_name")
                    parameters = step.get("parameters", {})

                    if tool_name not in self.tools:
                        raise ValueError(f"Tool '{tool_name}' not found.")

                    tool_instance = self.tools[tool_name]

                    logging.info(f"Executing step {step.get('step_id')}: {step.get('description')} with tool {tool_name}")

                    # Execute the tool and get the result
                    result = tool_instance.execute(**parameters)

                    # Update context
                    context.last_step_output = {"status": "success", "result": result}
                    current_step_data = {
                        "step_id": step.get("step_id"),
                        "description": step.get("description"),
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "output": context.last_step_output
                    }
                    context.step_history.append(current_step_data)
                    logging.info(f"Step {step.get('step_id')} completed successfully. Result: {result}")

                    # Broadcast success
                    await manager.broadcast({"type": "step_update", **current_step_data}, context.session_id)

                except Exception as e:
                    logging.error(f"Step {step.get('step_id')} failed: {e}")
                    plan_successful = False

                    # --- DEBUGGING AND REPAIR LOOP ---
                    context.last_step_output = {"status": "error", "error": str(e)}
                    failed_step_data = {
                         "step_id": step.get("step_id"),
                         "description": step.get("description"),
                         "tool_name": step.get("tool_name"),
                         "output": context.last_step_output
                    }
                    context.step_history.append(failed_step_data)

                    # Broadcast failure
                    await manager.broadcast({"type": "step_update", **failed_step_data}, context.session_id)

                    # Trigger the planner to repair the plan
                    logging.info("Calling PlannerAgent to repair the plan...")

                    repair_context = SharedContext(
                        original_prompt=f"The previous plan failed. Please create a new plan to achieve the original goal. Original goal: {context.original_prompt}. Failed plan: {context.current_plan}. The step that failed was '{step.get('description')}' with the error: {str(e)}",
                        session_id=context.session_id
                    )

                    repaired_context = self.planner.run_task(repair_context)
                    new_plan = repaired_context.payload.get("plan")

                    if new_plan:
                        logging.info("Received a new plan from the planner. Restarting execution.")
                        context.current_plan = new_plan
                        context.step_history = []
                        repair_attempts += 1
                        await manager.broadcast({"type": "plan_repaired", "new_plan": new_plan}, context.session_id)
                        break
                    else:
                        logging.error("Planner failed to provide a new plan. Aborting.")
                        context.feedback = "Execution aborted: Planner failed to repair the plan."
                        await manager.broadcast({"type": "plan_feedback", "feedback": context.feedback}, context.session_id)
                        return context

            if plan_successful:
                logging.info("Plan executed successfully.")
                context.feedback = "Plan executed successfully."
                await manager.broadcast({"type": "plan_feedback", "feedback": context.feedback}, context.session_id)
                return context

        logging.error(f"Failed to execute plan after {self.MAX_REPAIR_ATTEMPTS} repair attempts.")
        context.feedback = f"Execution failed after {self.MAX_REPAIR_ATTEMPTS} repair attempts."
        await manager.broadcast({"type": "plan_feedback", "feedback": context.feedback}, context.session_id)
        return context
