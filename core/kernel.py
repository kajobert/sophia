import asyncio
import json
import logging
import uuid
import copy
from pathlib import Path
from typing import Dict, Any

import yaml
from pydantic import ValidationError, Field, create_model

from core.context import SharedContext
from core.logging_config import SessionIdFilter, setup_logging
from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType

logger = logging.getLogger(__name__)


class Kernel:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.is_running = False
        self.all_plugins_map = {}
        self.tool_schemas = {}

    async def initialize(self):
        logger.info("Initializing plugin setup...", extra={"plugin_name": "Kernel"})
        all_plugins_list = [p for pt in PluginType for p in self.plugin_manager.get_plugins_by_type(pt)]
        self.all_plugins_map = {p.name: p for p in all_plugins_list}

        for plugin in all_plugins_list:
            config_path = Path("config/settings.yaml")
            main_config = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    main_config = yaml.safe_load(f) or {}

            plugin_configs = main_config.get("plugins", {})
            specific_config = plugin_configs.get(plugin.name, {})
            full_plugin_config = {**specific_config, "plugin_manager": self.plugin_manager, "plugins": self.all_plugins_map}

            try:
                plugin.setup(full_plugin_config)
                logger.info(f"Successfully set up plugin '{plugin.name}'.", extra={"plugin_name": "Kernel"})
            except Exception as e:
                logger.error(f"Error setting up plugin '{plugin.name}': {e}", exc_info=True, extra={"plugin_name": "Kernel"})

        self._build_tool_schemas()
        logger.info(f"All {len(all_plugins_list)} plugins configured and tool schemas built.", extra={"plugin_name": "Kernel"})

    def _build_tool_schemas(self):
        for plugin in self.all_plugins_map.values():
            if hasattr(plugin, "get_tool_definitions"):
                for tool_def in plugin.get_tool_definitions():
                    function = tool_def.get("function", {})
                    func_name = function.get("name")
                    params_schema = function.get("parameters")
                    if func_name and params_schema:
                        fields = {
                            prop_name: (
                                {"string": str, "integer": int, "number": float, "boolean": bool}.get(prop_def.get("type"), str),
                                Field(..., description=prop_def.get("description"))
                            )
                            for prop_name, prop_def in params_schema.get("properties", {}).items()
                        }
                        self.tool_schemas[func_name] = create_model(f"{func_name}ArgsModel", **fields)

    async def _get_user_input(self, context: SharedContext) -> str | None:
        context.payload = {}
        interface_plugins = self.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
        if not interface_plugins:
            await asyncio.sleep(5)
            return None

        input_tasks = [asyncio.create_task(p.execute(context)) for p in interface_plugins]
        try:
            done, pending = await asyncio.wait(input_tasks, return_when=asyncio.FIRST_COMPLETED, timeout=60.0)
            for task in pending:
                task.cancel()
            if done:
                res_context = await done.pop()
                return res_context.user_input
        except asyncio.TimeoutError:
            pass
        return None

    async def consciousness_loop(self, single_run_input: str | None = None):
        self.is_running = True
        session_id = str(uuid.uuid4())
        setup_logging(log_queue=asyncio.Queue())
        session_logger = logging.getLogger(f"session-{session_id[:8]}")
        session_logger.addFilter(SessionIdFilter(session_id))
        context = SharedContext(session_id=session_id, current_state="STARTING", logger=session_logger, history=[])

        main_goal: str | None = None
        current_plan: list = []
        step_outputs: Dict[int, Any] = {}

        while self.is_running:
            try:
                # 1. GOAL SETTING
                if not main_goal:
                    context.current_state = "LISTENING"
                    user_input = single_run_input or await self._get_user_input(context)
                    if user_input:
                        main_goal = user_input
                        context.user_input = main_goal
                        context.history.append({"role": "user", "content": main_goal})
                        session_logger.info(f"New goal set: {main_goal}", extra={"plugin_name": "Kernel"})
                    else:
                        await asyncio.sleep(0.1)
                        continue

                # 2. PLANNING
                if not current_plan:
                    context.current_state = "PLANNING"
                    planner = self.all_plugins_map.get("cognitive_planner")
                    if planner:
                        plan_context = await planner.execute(context)
                        current_plan = plan_context.payload.get("plan", [])
                        session_logger.info(f"Planner created a new plan with {len(current_plan)} steps.", extra={"plugin_name": "Kernel"})

                        if not current_plan:
                            final_response = f"Goal '{main_goal}' is complete."
                            if single_run_input:
                                print(f"Final output for single run: {final_response}")
                                self.is_running = False
                            else:
                                print(f">>> Sophia: {final_response}")
                                main_goal = None
                            continue
                    else:
                        session_logger.warning("Cognitive planner not found, cannot proceed with goal.", extra={"plugin_name": "Kernel"})
                        main_goal = None
                        continue

                # 3. EXECUTION
                if current_plan:
                    context.current_state = "EXECUTING"
                    step = current_plan.pop(0)
                    step_index = len(step_outputs) + 1
                    tool_name, method_name, arguments = step.get("tool_name"), step.get("method_name"), step.get("arguments", {})

                    try:
                        for arg, val in arguments.items():
                            if isinstance(val, str) and val.startswith("$result.step_"):
                                arguments[arg] = step_outputs[int(val.split("_")[-1])]

                        validation_model = self.tool_schemas.get(method_name)
                        validated_args = validation_model(**arguments).model_dump()

                        tool = self.all_plugins_map.get(tool_name)
                        method = getattr(tool, method_name, None)

                        import inspect
                        call_args = validated_args.copy()
                        if "context" in inspect.signature(method).parameters:
                            new_context = copy.deepcopy(context)
                            new_context.user_input = str(validated_args)
                            call_args["context"] = new_context

                        result = await method(**call_args) if asyncio.iscoroutinefunction(method) else method(**call_args)
                        output = result.payload.get("llm_response", result) if isinstance(result, SharedContext) else result
                        step_outputs[step_index] = output

                    except Exception as e:
                        session_logger.error(f"Step {step_index} ({tool_name}.{method_name}) failed: {e}", exc_info=True, extra={"plugin_name": "Kernel"})
                        context.history.append({"role": "system", "content": f"Execution failed for goal '{main_goal}'. Replanning."})
                        context.user_input = main_goal  # Restore the goal for the planner
                        current_plan.clear()
                        step_outputs.clear() # Clear previous step outputs to avoid inconsistent state
                        continue

                # 4. COMPLETION
                if not current_plan and main_goal:
                    final_response = f"Goal '{main_goal}' complete. Final result: {step_outputs.get(len(step_outputs), 'N/A')}"
                    session_logger.info(final_response, extra={"plugin_name": "Kernel"})

                    if single_run_input:
                        print(f"Final output for single run: {final_response}")
                        self.is_running = False
                    else:
                        print(f">>> Sophia: {final_response}")
                        main_goal = None

            except asyncio.CancelledError:
                self.is_running = False
            except Exception as e:
                session_logger.error(f"Critical error in consciousness loop: {e}", exc_info=True, extra={"plugin_name": "Kernel"})
                main_goal = None
                await asyncio.sleep(5)

    def start(self):
        try:
            asyncio.run(self.consciousness_loop())
        except KeyboardInterrupt:
            logger.info("Application terminated by user.", extra={"plugin_name": "Kernel"})
