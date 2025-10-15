import os
import importlib
import inspect
import logging
from typing import Dict, Any, Optional, List

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

    def __init__(
        self,
        llm: Optional[Any] = None,
        short_term_memory: Optional[ShortTermMemory] = None,
        reptilian_brain: Optional[Any] = None,
        mammalian_brain: Optional[Any] = None,
        planner: Optional[PlannerAgent] = None,
    ) -> None:
        """Constructor accepts multiple signatures for backward compatibility.

        Old callers/tests may pass (short_term_memory=..., planner=...) while
        newer callers may pass llm to build a PlannerAgent internally. Honor
        either pattern and prefer an explicitly provided planner.
        """
        # Planner: prefer explicit planner, otherwise build from llm if provided
        if planner is not None:
            self.planner = planner
        else:
            self.planner = PlannerAgent(llm) if llm is not None else PlannerAgent(llm)

        # Tools loader
        self.tools = self._load_tools()

        # Short-term memory (STM)
        self.stm = short_term_memory or ShortTermMemory()

        # Optional brain references (kept for compatibility/test inspection)
        self.reptilian_brain = reptilian_brain
        self.mammalian_brain = mammalian_brain

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

    async def execute_plan(self, context: SharedContext) -> SharedContext:
        """
        Execute the plan stored in context.current_plan. On step failure, request a
        targeted repair for that step and resume execution (do not restart entire plan).
        """
        repair_attempts: int = 0

        if not context.current_plan or not isinstance(context.current_plan, list):
            logger.error("No valid plan to execute. Aborting.")
            context.feedback = "Execution aborted: No plan provided."
            await manager.broadcast(
                {"type": "plan_feedback", "feedback": context.feedback},
                context.session_id,
            )
            return context

        # ensure short-term memory has the initial state
        try:
            # prefer save_state/load_state API for persistence so tests/mocks that
            # hook into save_state/load_state observe the stored state.
            self.stm.save_state(
                context.session_id,
                {"plan": context.current_plan, "step_history": context.step_history},
            )
        except Exception:
            # fallback to set if save_state not available
            try:
                self.stm.set(
                    context.session_id,
                    {"plan": context.current_plan, "step_history": context.step_history},
                )
            except Exception:
                logger.exception("Failed to persist initial STM state")

        i: int = 0
        current_plan: List[Dict[str, Any]] = context.current_plan or []
        while i < len(current_plan):
            step = current_plan[i]
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

                # persist progress (use save_state/load_state when possible so
                # mocks that track saved state see updates)
                try:
                    current: Dict[str, Any] = self.stm.load_state(context.session_id) or {}
                    current.update(
                        {
                            "last_executed_index": i,
                            "plan": current_plan,
                            "step_history": context.step_history,
                        }
                    )
                    self.stm.save_state(context.session_id, current)
                except Exception:
                    try:
                        self.stm.update(
                            context.session_id,
                            {
                                "last_executed_index": i,
                                "plan": context.current_plan,
                                "step_history": context.step_history,
                            },
                        )
                    except Exception:
                        logger.exception("Failed to persist STM progress")

                i += 1
                # sync local view of the plan in case it was updated elsewhere
                current_plan = context.current_plan or current_plan

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
                # persist repair attempt count so tests/mocks can observe it
                try:
                    current = self.stm.load_state(context.session_id) or {}
                    current["repair_attempts"] = repair_attempts
                    self.stm.save_state(context.session_id, current)
                except Exception:
                    try:
                        self.stm.update(context.session_id, {"repair_attempts": repair_attempts})
                    except Exception:
                        logger.exception("Failed to persist repair attempt count to STM")
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
                # planner may return SharedContext or dict-like
                if hasattr(repaired, "payload"):
                    new_steps = repaired.payload.get("plan")
                elif isinstance(repaired, dict):
                    new_steps = repaired.get("payload", {}).get("plan")
                else:
                    new_steps = None

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
                    if len(context.current_plan or []) == 1 and len(new_steps or []) > 1:
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
                        # refresh local plan view so the loop iterates the new plan
                        current_plan = context.current_plan or []
                        continue

                    # Otherwise, treat returned steps as replacements for the failing step (splice-in)
                    logger.info(
                        "Applying repaired step(s) into the current plan (splice-in)."
                    )
                    # For splice-in repairs we should preserve previously successful steps.
                    # We only remove the failure entry we just appended so earlier successes remain.
                    if context.step_history and context.step_history[-1].get("output", {}).get("status") == "error":
                        try:
                            context.step_history.pop()
                        except Exception:
                            # If popping fails for any reason, fall back to clearing to avoid inconsistent state
                            context.step_history = []
                    context.current_plan = (
                        (context.current_plan or [])[:i]
                        + (new_steps or [])
                        + (context.current_plan or [])[i + 1 :]
                    )
                    # persist updated plan and cleared history
                    try:
                        current = self.stm.load_state(context.session_id) or {}
                        current.update({"plan": context.current_plan, "step_history": context.step_history})
                        self.stm.save_state(context.session_id, current)
                    except Exception:
                        try:
                            self.stm.update(context.session_id, {"plan": context.current_plan, "step_history": context.step_history})
                        except Exception:
                            logger.exception("Failed to persist updated plan after repair")

                    # refresh local plan view and reset repair attempts so we run the
                    # newly inserted steps and don't immediately abort due to prior attempts
                    current_plan = context.current_plan or []
                    repair_attempts = 0
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

    async def process_input(self, session_id: str, user_input: str) -> SharedContext:
        """High-level convenience method used by tests: builds a SharedContext,
        runs the planner (via Neocortex.process_input flow) and executes the plan.
        This keeps compatibility with older test expectations.
        """
        ctx = SharedContext(session_id=session_id, original_prompt=user_input)

        # Optionally run reptilian brain (tests expect it to be called with raw input)
        reptilian_out = None
        try:
            if getattr(self, "reptilian_brain", None):
                reptilian_out = self.reptilian_brain.process_input(user_input)
                # If the brain returns a dict, merge into payload
                if isinstance(reptilian_out, dict):
                    ctx.payload.setdefault("reptilian", {}).update(reptilian_out)
                elif isinstance(reptilian_out, SharedContext):
                    ctx = reptilian_out
        except Exception:
            logger.exception("Reptilian brain processing failed")

        # Optionally run mammalian brain (tests may pass dicts)
        try:
            if getattr(self, "mammalian_brain", None):
                # pass either the reptilian output or the SharedContext.payload
                mammalian_input = reptilian_out if reptilian_out is not None else ctx.payload
                mammalian_out = self.mammalian_brain.process_input(mammalian_input)
                if isinstance(mammalian_out, dict):
                    ctx.payload.setdefault("mammalian", {}).update(mammalian_out)
                elif isinstance(mammalian_out, SharedContext):
                    ctx = mammalian_out
        except Exception:
            logger.exception("Mammalian brain processing failed")

        # If planner available, ask for a plan
        if self.planner:
            try:
                plan_ctx = self.planner.run_task(ctx)
                # plan_ctx may be a SharedContext or a dict-like object
                if hasattr(plan_ctx, "payload"):
                    ctx.current_plan = plan_ctx.payload.get("plan")
                elif isinstance(plan_ctx, dict):
                    ctx.current_plan = plan_ctx.get("payload", {}).get("plan")
                else:
                    ctx.current_plan = None
            except Exception:
                logger.exception("Planner failed to produce a plan")
                ctx.current_plan = []

        # execute the plan
        return await self.execute_plan(ctx)
