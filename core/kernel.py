import asyncio
import logging
import uuid
import yaml
from pathlib import Path
from core.context import SharedContext
from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType

# Basic logging setup for Kernel execution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Kernel:
    """
    Manages the main lifecycle (Consciousness Loop), state, and orchestrates
    plugin execution.
    """

    def __init__(self):
        self.plugin_manager = PluginManager()
        self.is_running = False

    async def consciousness_loop(self):
        """The main, infinite loop that keeps Sophia "conscious"."""
        self.is_running = True
        session_id = str(uuid.uuid4())

        # --- PLUGIN SETUP PHASE ---
        logger.info("Initializing plugin setup...")
        all_plugins_list = [
            p for pt in PluginType for p in self.plugin_manager.get_plugins_by_type(pt)
        ]
        all_plugins_map = {p.name: p for p in all_plugins_list}

        # Pass configuration and dependencies to all plugins
        for plugin in all_plugins_list:
            config_path = Path("config/settings.yaml")
            if not config_path.exists():
                logger.warning("Config 'config/settings.yaml' not found during loop setup.")
                main_config = {}
            else:
                with open(config_path, "r") as f:
                    main_config = yaml.safe_load(f) or {}
            plugin_configs = main_config.get("plugins", {})
            specific_config = plugin_configs.get(plugin.name, {})

            full_plugin_config = {
                **specific_config,
                "plugin_manager": self.plugin_manager,
                "plugins": all_plugins_map,
            }
            try:
                plugin.setup(full_plugin_config)
                logger.info(f"Successfully set up plugin '{plugin.name}'.")
            except Exception as e:
                logger.error(f"Error setting up plugin '{plugin.name}': {e}", exc_info=True)

        logger.info(f"All {len(all_plugins_list)} plugins have been configured.")
        # --- END PLUGIN SETUP PHASE ---

        context = SharedContext(
            session_id=session_id,
            current_state="INITIALIZING",
            logger=logging.getLogger(f"session-{session_id[:8]}"),
            history=[],
        )

        while self.is_running:
            try:
                # 1. LISTENING PHASE
                context.current_state = "LISTENING"
                context.user_input = None
                context.payload = {}
                interface_plugins = self.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)

                if not interface_plugins:
                    logger.warning("No INTERFACE plugins found. Waiting...")
                    await asyncio.sleep(5)
                    continue

                input_tasks = [asyncio.create_task(p.execute(context)) for p in interface_plugins]

                try:
                    done, pending = await asyncio.wait(
                        input_tasks,
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=60.0,
                    )

                    for task in pending:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

                    if done:
                        first_done_task = done.pop()
                        if not first_done_task.cancelled():
                            context = await first_done_task
                        else:
                            logger.warning("Input task was cancelled unexpectedly.")
                            context.user_input = None
                    else:
                        context.user_input = None

                except asyncio.TimeoutError:
                    logger.debug("Listening timed out, no user input received.")
                    context.user_input = None
                    for task in input_tasks:
                        if not task.done():
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass

                if context.user_input:
                    logger.info(f"User input received: '{context.user_input}'")
                    context.history.append({"role": "user", "content": context.user_input})

                    # 2. PLANNING PHASE
                    context.current_state = "PLANNING"
                    planner = all_plugins_map.get("cognitive_planner")
                    plan = []
                    if planner:
                        context = await planner.execute(context)
                        plan = context.payload.get("plan", [])
                        if not isinstance(plan, list):
                            logger.error(
                                f"Planner returned invalid plan: {plan}. Defaulting to empty."
                            )
                            plan = []
                    else:
                        logger.warning("Cognitive planner plugin not found.")

                    # 3. EXECUTING PHASE
                    context.current_state = "EXECUTING"
                    execution_summary = ""
                    if plan:
                        logger.info(f"Executing plan: {plan}")
                        step_results = []
                        for step_index, step in enumerate(plan):
                            tool_name = step.get("tool_name")
                            method_name = step.get("method_name")
                            arguments = step.get("arguments", {})

                            tool = all_plugins_map.get(tool_name)
                            method = None
                            step_result = None

                            if tool and hasattr(tool, method_name):
                                method = getattr(tool, method_name, None)

                            if method:
                                logger.info(
                                    f"Executing Step {step_index + 1}/{len(plan)}: "
                                    f"{tool_name}.{method_name}({arguments})"
                                )
                                try:
                                    if asyncio.iscoroutinefunction(method):
                                        step_result = await method(**arguments)
                                    else:
                                        step_result = method(**arguments)
                                    step_results.append(str(step_result))
                                    logger.info(
                                        f"Step '{method_name}' executed. Result: {step_result}"
                                    )
                                except Exception as exec_err:
                                    error_message = (
                                        f"Error executing {tool_name}.{method_name}: {exec_err}"
                                    )
                                    logger.error(error_message, exc_info=True)
                                    step_results.append(error_message)
                                    execution_summary = (
                                        f"Plan failed at step {step_index + 1}. "
                                        f"Error: {error_message}"
                                    )
                                    break
                            else:
                                error_message = (
                                    f"Error: Tool '{tool_name}' or method "
                                    f"'{method_name}' not found."
                                )
                                logger.error(error_message)
                                step_results.append(error_message)
                                execution_summary = (
                                    f"Plan failed at step {step_index + 1}. {error_message}"
                                )
                                break

                        if not execution_summary:
                            execution_summary = (
                                "Plan executed successfully. Result: " + " | ".join(step_results)
                            )

                    else:
                        llm_tool = all_plugins_map.get("tool_llm")
                        if llm_tool:
                            logger.info("No plan generated, attempting direct LLM response.")
                            context = await llm_tool.execute(context)
                            execution_summary = context.payload.get(
                                "llm_response", "Input received, no plan formed."
                            )
                        else:
                            execution_summary = (
                                "Input received, but no planner or LLM tool is configured."
                            )
                            logger.warning("No plan and no LLM tool found for direct response.")

                    # 4. RESPONDING PHASE
                    context.current_state = "RESPONDING"
                    context.payload["final_response"] = execution_summary
                    logger.info(f"Final response: {execution_summary}")
                    context.history.append({"role": "assistant", "content": execution_summary})

                    response_callback = context.payload.get("_response_callback")
                    if response_callback:
                        try:
                            if asyncio.iscoroutinefunction(response_callback):
                                await response_callback(execution_summary)
                            else:
                                response_callback(execution_summary)
                        except Exception as cb_err:
                            logger.error(
                                f"Error in response callback: {cb_err}",
                                exc_info=True,
                            )
                    else:
                        print(f">>> Sophia: {execution_summary}")

                    # 5. MEMORIZING PHASE
                    context.current_state = "MEMORIZING"
                    memory_plugins = self.plugin_manager.get_plugins_by_type(PluginType.MEMORY)
                    memorizing_tasks = []
                    for mem_plugin in memory_plugins:
                        memorizing_tasks.append(asyncio.create_task(mem_plugin.execute(context)))

                    if memorizing_tasks:
                        await asyncio.wait(memorizing_tasks)

                else:
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info("Consciousness loop cancelled.")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error in consciousness loop: {e}", exc_info=True)
                await asyncio.sleep(5)

        logger.info("Consciousness loop finished.")

    def start(self):
        """Starts the main consciousness loop."""
        try:
            asyncio.run(self.consciousness_loop())
        except KeyboardInterrupt:
            logger.info("Application terminated by user (Ctrl+C).")
