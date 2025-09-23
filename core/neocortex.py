import os
import importlib
import inspect
import logging
from typing import Dict

from core.context import SharedContext
from core.memory_systems import ShortTermMemory
from agents.planner_agent import PlannerAgent
from tools.base_tool import BaseTool
from services.websocket_manager import manager
from core.llm_config import llm

logger = logging.getLogger(__name__)


class Neocortex:
    """
    Neocortex: executes plans, uses short-term memory, and repairs failing steps without
    re-running already successful steps.
    """

    MAX_REPAIR_ATTEMPTS = 3

    def __init__(self, llm, short_term_memory: ShortTermMemory = None):
        self.planner = PlannerAgent(llm)
        self.tools = self._load_tools()
        self.stm = short_term_memory or ShortTermMemory()

    def _load_tools(self) -> Dict[str, BaseTool]:
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
                            try:
                                tools[name] = cls()
                                logger.info(f"Successfully loaded tool: {name}")
                            except Exception as e:
                                logger.error(f"Failed to instantiate tool {name}: {e}")
                except Exception as e:
                    logger.error(f"Failed to load module {module_name}: {e}")
        return tools

    async def execute_plan(self, context: SharedContext):
        """
        Execute the plan stored in context.current_plan. On step failure, request a
        targeted repair for that step and resume execution (do not restart entire plan).
        """
        repair_attempts = 0

        if not context.current_plan or not isinstance(context.current_plan, list):
            logger.error("No valid plan to execute. Aborting.")
            context.feedback = "Execution aborted: No plan provided."
            await manager.broadcast(
                {"type": "plan_feedback", "feedback": context.feedback},
                context.session_id,
            )
            return context

        # ensure short-term memory has the initial state
        self.stm.set(
            context.session_id,
            {"plan": context.current_plan, "step_history": context.step_history},
        )

        i = 0
        while i < len(context.current_plan):
            step = context.current_plan[i]
            try:
                tool_name = step.get("tool_name")
                parameters = step.get("parameters", {})

                if tool_name not in self.tools:
                    raise ValueError(f"Tool '{tool_name}' not found.")

                tool_instance = self.tools[tool_name]
                logger.info(
                    f"Executing step {step.get('step_id')}: {step.get('description')} with tool {tool_name}"
                )

                result = tool_instance.execute(**parameters)

                # Update context
                context.last_step_output = {"status": "success", "result": result}
                current_step_data = {
                    "step_id": step.get("step_id"),
                    "description": step.get("description"),
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "output": context.last_step_output,
                }
                context.step_history.append(current_step_data)
                logger.info(
                    f"Step {step.get('step_id')} completed successfully. Result: {result}"
                )

                await manager.broadcast(
                    {"type": "step_update", **current_step_data}, context.session_id
                )

                # persist progress
                self.stm.update(
                    context.session_id,
                    {
                        "last_executed_index": i,
                        "plan": context.current_plan,
                        "step_history": context.step_history,
                    },
                )

                i += 1

            except Exception as e:
                logger.error(f"Step {step.get('step_id')} failed: {e}")
                context.last_step_output = {"status": "error", "error": str(e)}
                failed_step_data = {
                    "step_id": step.get("step_id"),
                    "description": step.get("description"),
                    "tool_name": step.get("tool_name"),
                    "output": context.last_step_output,
                }
                context.step_history.append(failed_step_data)
                await manager.broadcast(
                    {"type": "step_update", **failed_step_data}, context.session_id
                )

                # attempt repair for this specific step
                repair_attempts += 1
                if repair_attempts > self.MAX_REPAIR_ATTEMPTS:
                    logger.error("Exceeded max repair attempts for a step. Aborting.")
                    context.feedback = f"Execution failed after {self.MAX_REPAIR_ATTEMPTS} repair attempts for a step."
                    await manager.broadcast(
                        {"type": "plan_feedback", "feedback": context.feedback},
                        context.session_id,
                    )
                    return context

                # build a focused repair prompt
                repair_prompt = (
                    f"The following plan step failed: {step}. "
                    f"Error: {str(e)}. Please propose a replacement for this step only, "
                    f"keeping the rest of the plan unchanged. Return a JSON array of steps if replacement is more than one step."
                )

                repair_context = SharedContext(
                    original_prompt=repair_prompt, session_id=context.session_id
                )
                repaired = self.planner.run_task(repair_context)
                new_steps = repaired.payload.get("plan")

                # DEBUG: if planner returned nothing or an invalid plan, log the raw payload for inspection
                if not new_steps:
                    try:
                        self.logger = logger
                        logger.debug(
                            f"Planner raw payload during repair: {repaired.payload}"
                        )
                    except Exception:
                        logger.debug("Planner returned no payload or payload is not inspectable.")

                if new_steps:
                    # If original plan was a single step and planner returned multiple steps,
                    # treat the returned plan as a full replacement (legacy behavior).
                    if len(context.current_plan) == 1 and len(new_steps) > 1:
                        logger.info(
                            "Applying repaired plan as full replacement and restarting execution."
                        )
                        context.current_plan = new_steps
                        context.step_history = []
                        # persist updated plan
                        self.stm.update(
                            context.session_id,
                            {
                                "plan": context.current_plan,
                                "step_history": context.step_history,
                            },
                        )
                        # restart execution from the beginning
                        i = 0
                        repair_attempts = 0
                        continue

                    # Otherwise, treat returned steps as replacements for the failing step (splice-in)
                    logger.info(
                        "Applying repaired step(s) into the current plan (splice-in)."
                    )
                    context.current_plan = (
                        context.current_plan[:i]
                        + new_steps
                        + context.current_plan[i + 1 :]
                    )
                    # persist updated plan
                    self.stm.update(context.session_id, {"plan": context.current_plan})
                    # do not increment i — re-run at the same index which now points to first new step
                    continue
                else:
                    logger.error(
                        "Planner failed to provide a repair for the step. Aborting."
                    )
                    context.feedback = (
                        "Execution aborted: Planner failed to repair the step."
                    )
                    await manager.broadcast(
                        {"type": "plan_feedback", "feedback": context.feedback},
                        context.session_id,
                    )
                    return context

        logger.info("Plan executed successfully.")
        context.feedback = "Plan executed successfully."
        await manager.broadcast(
            {"type": "plan_feedback", "feedback": context.feedback}, context.session_id
        )
        return context
