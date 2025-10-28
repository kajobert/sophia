import asyncio
import json
import logging
import yaml
from pathlib import Path

from pydantic import ValidationError

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
        self.json_repair_prompt_template = ""
        self.all_plugins_map = {}

    async def initialize(self):
        """Loads prompts, discovers, and sets up all plugins."""
        # --- PROMPT LOADING PHASE ---
        try:
            with open("config/prompts/json_repair_prompt.txt", "r") as f:
                self.json_repair_prompt_template = f.read()
        except FileNotFoundError:
            logger.error("JSON repair prompt template not found. The repair loop will fail.")
            self.json_repair_prompt_template = "The JSON is invalid. Errors: {e}. Please fix it."

        # --- PLUGIN SETUP PHASE ---
        logger.info("Initializing plugin setup...")
        all_plugins_list = [
            p for pt in PluginType for p in self.plugin_manager.get_plugins_by_type(pt)
        ]
        self.all_plugins_map = {p.name: p for p in all_plugins_list}

        for plugin in all_plugins_list:
            config_path = Path("config/settings.yaml")
            if not config_path.exists():
                logger.warning("Config 'config/settings.yaml' not found.")
                main_config = {}
            else:
                with open(config_path, "r") as f:
                    main_config = yaml.safe_load(f) or {}
            plugin_configs = main_config.get("plugins", {})
            specific_config = plugin_configs.get(plugin.name, {})

            full_plugin_config = {
                **specific_config,
                "plugin_manager": self.plugin_manager,
                "plugins": self.all_plugins_map,
            }
            try:
                plugin.setup(full_plugin_config)
                logger.info(f"Successfully set up plugin '{plugin.name}'.")
            except Exception as e:
                logger.error(f"Error setting up plugin '{plugin.name}': {e}", exc_info=True)

        logger.info(f"All {len(all_plugins_list)} plugins have been configured.")

    async def consciousness_loop(self):
        """The main, infinite loop that keeps Sophia "conscious"."""
        self.is_running = True
        session_id = str(uuid.uuid4())

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
                    planner = self.all_plugins_map.get("cognitive_planner")
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
                    llm_tool = self.all_plugins_map.get("tool_llm")

                    if plan:
                        logger.info(f"Initiating execution for raw plan: {plan}")

                        # --- GATHER ALL TOOL DEFINITIONS AND VALIDATION SCHEMAS ---
                        from pydantic import create_model, Field

                        tool_schemas = {}
                        all_plugins = self.all_plugins_map.values()
                        for plugin in all_plugins:
                            if hasattr(plugin, "get_tool_definitions"):
                                for tool_def in plugin.get_tool_definitions():
                                    function = tool_def.get("function", {})
                                    func_name = function.get("name")
                                    params_schema = function.get("parameters")
                                    if func_name and params_schema:
                                        fields = {}
                                        for prop_name, prop_def in params_schema.get(
                                            "properties", {}
                                        ).items():
                                            field_type = {
                                                "string": str,
                                                "integer": int,
                                                "number": float,
                                                "boolean": bool,
                                            }.get(prop_def.get("type"), str)
                                            desc = prop_def.get("description")
                                            fields[prop_name] = (
                                                field_type,
                                                Field(..., description=desc),
                                            )

                                        validation_model = create_model(
                                            f"{func_name}ArgsModel", **fields
                                        )
                                        tool_schemas[func_name] = validation_model

                        step_results = []
                        plan_failed = False
                        for step_index, step in enumerate(plan):
                            tool_name = step.get("tool_name")
                            method_name = step.get("method_name")
                            arguments = step.get("arguments", {})

                            validated_args = None
                            max_attempts = 3  # 1 initial + 2 retries

                            for attempt in range(max_attempts):
                                try:
                                    validation_model = tool_schemas.get(method_name)
                                    if not validation_model:
                                        msg = f"No validation schema found for method '{method_name}'."
                                        raise ValueError(msg)

                                    current_args = arguments
                                    if isinstance(current_args, str):
                                        try:
                                            current_args = json.loads(current_args)
                                        except json.JSONDecodeError:
                                            msg = f"Arguments are a non-JSON string: {current_args}"
                                            raise ValueError(msg)

                                    validated_args = validation_model(**current_args).dict()
                                    # fmt: off
                                    logger.info("SECOND-PHASE LOG: Validated plan step %d: %s.%s(%s)", step_index + 1, tool_name, method_name, validated_args)  # noqa: E501
                                    # fmt: on
                                    break  # Success

                                except (ValidationError, ValueError) as e:
                                    # fmt: off
                                    logger.warning("Validation failed for step %d (Attempt %d/%d): %s", step_index + 1, attempt + 1, max_attempts, e)  # noqa: E501
                                    # fmt: on
                                    if attempt + 1 == max_attempts:
                                        # fmt: off
                                        error_message = (
                                            f"Plan failed at step {step_index + 1} "
                                            f"after {max_attempts} attempts. Final error: {e}"
                                        )
                                        # fmt: on
                                        logger.error(error_message)
                                        step_results.append(error_message)
                                        plan_failed = True
                                        break

                                    if not llm_tool:
                                        error_message = "Cannot attempt repair: LLMTool not found."
                                        logger.error(error_message)
                                        step_results.append(error_message)
                                        plan_failed = True
                                        break

                                    repair_prompt = self.json_repair_prompt_template.format(
                                        tool_name=tool_name,
                                        method_name=method_name,
                                        arguments=arguments,
                                        e=e,
                                        user_input=context.user_input,
                                    )

                                    repair_context = await llm_tool.execute(
                                        SharedContext(
                                            session_id=context.session_id,
                                            current_state="EXECUTING",
                                            logger=context.logger,
                                            user_input=repair_prompt,
                                            history=[{"role": "user", "content": repair_prompt}], # TOTO JE TA KLÍČOVÁ OPRAVA
                                        )
                                    )
                                    
                                    arguments = repair_context.payload.get("llm_response")
                                    # fmt: off
                                    logger.info("Received repaired arguments for step %d: %s", step_index + 1, arguments)  # noqa: E501
                                    # fmt: on

                            if plan_failed or validated_args is None:
                                execution_summary = f"Plan failed at step {step_index + 1}."
                                break

                            # --- EXECUTION OF VALIDATED STEP ---
                            tool = self.all_plugins_map.get(tool_name)
                            method = getattr(tool, method_name, None) if tool else None
                            if method:
                                try:
                                    step_result = (
                                        await method(**validated_args)
                                        if asyncio.iscoroutinefunction(method)
                                        else method(**validated_args)
                                    )
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
                                    f"Error: Tool '{tool_name}' or method '{method_name}' "
                                    "not found."
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
                        # After printing to the console, re-display the user prompt.
                        terminal = self.all_plugins_map.get("interface_terminal")
                        if terminal and hasattr(terminal, "prompt"):
                            terminal.prompt()

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
