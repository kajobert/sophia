import os
import importlib
import inspect
import logging
from typing import Dict, Any, Optional, List

from core.context import SharedContext
from core.memory_systems import ShortTermMemory, get_stm
from tools.base_tool import BaseTool
from services.websocket_manager import manager
from core.llm_config import llm

logger = logging.getLogger(__name__)


class Neocortex:
    MAX_REPAIR_ATTEMPTS = 3

    def __init__(
        self,
        llm: Optional[Any] = None,
        short_term_memory: Optional[ShortTermMemory] = None,
        reptilian_brain: Optional[Any] = None,
        mammalian_brain: Optional[Any] = None,
    ) -> None:
        """Constructor for Neocortex."""
        self.tools = self._load_tools()
        self.stm = short_term_memory or get_stm()
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
        if not context.current_plan or not isinstance(context.current_plan, list):
            logger.error("No valid plan to execute. Aborting.")
            context.feedback = "Execution aborted: No plan provided."
            await manager.broadcast(
                {"type": "plan_feedback", "feedback": context.feedback},
                context.session_id,
            )
            return context

        for step in context.current_plan:
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
                context.feedback = f"Execution failed at step {step.get('step_id')}: {e}"
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

    async def process_input(self, context: SharedContext) -> SharedContext:
        return await self.execute_plan(context)