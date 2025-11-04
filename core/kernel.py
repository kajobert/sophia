import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from pydantic import ValidationError

from core.context import SharedContext
from core.logging_config import SessionIdFilter, setup_logging
from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType

# Get the root logger
logger = logging.getLogger(__name__)


class Kernel:
    """
    Manages the main lifecycle (Consciousness Loop), state, and orchestrates
    plugin execution.
    """

    def __init__(self, use_event_driven: bool = False):
        """
        Initialize Kernel.
        
        Args:
            use_event_driven: If True, enable event-driven architecture (Phase 1)
        """
        self.plugin_manager = PluginManager()
        self.is_running = False
        self.json_repair_prompt_template = ""
        self.all_plugins_map = {}
        self.memory = None  # Will be set during initialization
        
        # NEW: Event-driven components (Phase 1)
        self.use_event_driven = use_event_driven
        self.event_bus = None
        self.task_queue = None

    async def initialize(self):
        """Loads prompts, discovers, and sets up all plugins."""
        # --- PROMPT LOADING PHASE ---
        try:
            with open("config/prompts/json_repair_prompt.txt", "r") as f:
                self.json_repair_prompt_template = f.read()
        except FileNotFoundError:
            logger.error(
                "JSON repair prompt template not found. The repair loop will fail.",
                extra={"plugin_name": "Kernel"},
            )
            self.json_repair_prompt_template = "The JSON is invalid. Errors: {e}. Please fix it."

        # NEW: Initialize Event-Driven Architecture (if enabled)
        if self.use_event_driven:
            from core.event_bus import EventBus
            from core.task_queue import TaskQueue
            from core.events import Event, EventType, EventPriority
            
            self.event_bus = EventBus()
            await self.event_bus.start()
            
            self.task_queue = TaskQueue(event_bus=self.event_bus, max_workers=5)
            await self.task_queue.start()
            
            logger.info(
                "Event-driven architecture enabled - EventBus and TaskQueue started",
                extra={"plugin_name": "Kernel"}
            )
            
            # Publish startup event
            self.event_bus.publish(Event(
                event_type=EventType.SYSTEM_STARTUP,
                source="kernel",
                priority=EventPriority.HIGH,
                data={"use_event_driven": True, "max_workers": 5}
            ))

        # --- PLUGIN SETUP PHASE ---
        logger.info("Initializing plugin setup...", extra={"plugin_name": "Kernel"})
        all_plugins_list = [
            p for pt in PluginType for p in self.plugin_manager.get_plugins_by_type(pt)
        ]
        self.all_plugins_map = {p.name: p for p in all_plugins_list}
        
        # Get memory plugin for state persistence
        memory_plugins = self.plugin_manager.get_plugins_by_type(PluginType.MEMORY)
        if memory_plugins:
            self.memory = memory_plugins[0]  # Use first available memory plugin
            logger.info(
                f"Using memory plugin: {self.memory.name}",
                extra={"plugin_name": "Kernel"},
            )
        else:
            logger.warning(
                "No memory plugin found - state persistence disabled",
                extra={"plugin_name": "Kernel"},
            )

        for plugin in all_plugins_list:
            config_path = Path("config/settings.yaml")
            if not config_path.exists():
                logger.warning(
                    "Config 'config/settings.yaml' not found.",
                    extra={"plugin_name": "Kernel"},
                )
                main_config = {}
            else:
                with open(config_path, "r") as f:
                    main_config = yaml.safe_load(f) or {}
            plugin_configs = main_config.get("plugins", {})
            specific_config = plugin_configs.get(plugin.name, {})

            # Create plugin-specific logger
            plugin_logger = logging.getLogger(f"plugin.{plugin.name}")

            full_plugin_config = {
                **specific_config,
                "plugin_manager": self.plugin_manager,
                "all_plugins": self.all_plugins_map,  # Pass all plugins for dependency injection
                "logger": plugin_logger,  # Inject logger per Development Guidelines
            }
            try:
                plugin.setup(full_plugin_config)
                logger.info(
                    f"Successfully set up plugin '{plugin.name}'.",
                    extra={"plugin_name": "Kernel"},
                )
            except Exception as e:
                logger.error(
                    f"Error setting up plugin '{plugin.name}': {e}",
                    exc_info=True,
                    extra={"plugin_name": "Kernel"},
                )

        logger.info(
            f"All {len(all_plugins_list)} plugins have been configured.",
            extra={"plugin_name": "Kernel"},
        )
        
        # --- PHASE 3: MEMORY CONSOLIDATION INTEGRATION ---
        if self.use_event_driven and self.event_bus:
            # Find Phase 3 plugins
            sleep_scheduler = self.all_plugins_map.get("core_sleep_scheduler")
            consolidator = self.all_plugins_map.get("cognitive_memory_consolidator")
            
            if sleep_scheduler and consolidator:
                # Wire dependencies
                sleep_scheduler.set_event_bus(self.event_bus)
                sleep_scheduler.set_consolidator(consolidator)
                consolidator.event_bus = self.event_bus
                
                # Start sleep scheduler
                await sleep_scheduler.start()
                
                logger.info(
                    "Phase 3 Memory Consolidation enabled - sleep scheduler active",
                    extra={"plugin_name": "Kernel"}
                )
            elif sleep_scheduler or consolidator:
                logger.warning(
                    f"Phase 3 partial: scheduler={bool(sleep_scheduler)}, consolidator={bool(consolidator)}",
                    extra={"plugin_name": "Kernel"}
                )

    async def consciousness_loop(self, single_run_input: str | None = None):
        """The main, infinite loop that keeps Sophia "conscious"."""
        self.is_running = True
        session_id = str(uuid.uuid4())

        setup_logging(log_queue=asyncio.Queue())  # Setup logging with queue
        session_logger = logging.getLogger(f"session-{session_id[:8]}")
        session_logger.addFilter(SessionIdFilter(session_id))

        context = SharedContext(
            session_id=session_id,
            current_state="INITIALIZING",
            logger=session_logger,
            history=[],
            # NEW: Add event-driven components to context
            event_bus=self.event_bus,
            task_queue=self.task_queue,
            use_event_driven=self.use_event_driven,
        )
        
        # Publish SYSTEM_READY event if event-driven
        if self.use_event_driven:
            from core.events import Event, EventType, EventPriority
            self.event_bus.publish(Event(
                event_type=EventType.SYSTEM_READY,
                source="kernel",
                priority=EventPriority.HIGH,
                data={"session_id": session_id}
            ))
            
            # Use event-driven loop (Phase 1 implementation)
            from core.event_loop import EventDrivenLoop
            
            event_loop = EventDrivenLoop(
                plugin_manager=self.plugin_manager,
                all_plugins_map=self.all_plugins_map,
                event_bus=self.event_bus,
                task_queue=self.task_queue
            )
            
            logger.info(
                "Using event-driven consciousness loop (Phase 1)",
                extra={"plugin_name": "Kernel"}
            )
            
            await event_loop.run(context, single_run_input)
            
            # Graceful shutdown
            await self._shutdown_event_system(context, session_id)
            
            return

        # Legacy blocking mode (original behavior)
        while self.is_running:
            try:
                # 1. LISTENING PHASE
                context.current_state = "LISTENING"

                if single_run_input:
                    context.user_input = single_run_input
                    self.is_running = False  # End the loop after this run
                    
                    # IMPORTANT: Still call interface plugins to register callbacks!
                    interface_plugins = self.plugin_manager.get_plugins_by_type(
                        PluginType.INTERFACE
                    )
                    for plugin in interface_plugins:
                        await plugin.execute(context=context)
                else:
                    context.user_input = None
                    context.payload = {}
                    interface_plugins = self.plugin_manager.get_plugins_by_type(
                        PluginType.INTERFACE
                    )

                    if not interface_plugins:
                        context.logger.warning(
                            "No INTERFACE plugins found. Waiting...",
                            extra={"plugin_name": "Kernel"},
                        )
                        await asyncio.sleep(5)
                        continue

                    input_tasks = [
                        asyncio.create_task(p.execute(context)) for p in interface_plugins
                    ]

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
                                context.logger.warning(
                                    "Input task was cancelled unexpectedly.",
                                    extra={"plugin_name": "Kernel"},
                                )
                                context.user_input = None
                        else:
                            context.user_input = None

                    except asyncio.TimeoutError:
                        context.logger.debug(
                            "Listening timed out, no user input received.",
                            extra={"plugin_name": "Kernel"},
                        )
                        context.user_input = None
                        for task in input_tasks:
                            if not task.done():
                                task.cancel()
                                try:
                                    await task
                                except asyncio.CancelledError:
                                    pass

                if context.user_input:
                    context.logger.info(
                        f"User input received: '{context.user_input}'",
                        extra={"plugin_name": "Kernel"},
                    )
                    context.history.append({"role": "user", "content": context.user_input})
                    
                    # NEW: Publish USER_INPUT event if event-driven
                    if self.use_event_driven:
                        from core.events import Event, EventType, EventPriority
                        self.event_bus.publish(Event(
                            event_type=EventType.USER_INPUT,
                            source="kernel",
                            priority=EventPriority.HIGH,
                            data={
                                "input": context.user_input,
                                "session_id": session_id
                            },
                            metadata={
                                "timestamp": datetime.now().isoformat()
                            }
                        ))

                    # 2. PLANNING PHASE
                    context.current_state = "PLANNING"

                    # --- Cognitive Task Routing ---
                    router = self.all_plugins_map.get("cognitive_task_router")
                    if router:
                        try:
                            context = await router.execute(context=context)
                            context.logger.info(
                                "Cognitive Task Router executed successfully.",
                                extra={"plugin_name": "Kernel"},
                            )
                        except Exception as e:
                            context.logger.error(
                                f"Error executing Cognitive Task Router: {e}",
                                extra={"plugin_name": "Kernel"},
                            )

                    planner = self.all_plugins_map.get("cognitive_planner")
                    plan = []
                    if planner:
                        context = await planner.execute(context)
                        plan = context.payload.get("plan", [])
                        if not isinstance(plan, list):
                            context.logger.error(
                                f"Planner returned invalid plan: {plan}. Defaulting to empty.",
                                extra={"plugin_name": "Kernel"},
                            )
                            plan = []
                    else:
                        context.logger.warning(
                            "Cognitive planner plugin not found.",
                            extra={"plugin_name": "Kernel"},
                        )

                    # 3. EXECUTING PHASE
                    context.current_state = "EXECUTING"
                    execution_summary = ""
                    llm_tool = self.all_plugins_map.get("tool_llm")

                    if plan:
                        context.logger.info(
                            f"Initiating execution for raw plan: {plan}",
                            extra={"plugin_name": "Kernel"},
                        )

                        # --- GATHER ALL TOOL DEFINITIONS AND VALIDATION SCHEMAS ---
                        from pydantic import Field, create_model

                        tool_schemas = {}
                        all_plugins_list = [
                            p
                            for pt in PluginType
                            for p in self.plugin_manager.get_plugins_by_type(pt)
                        ]
                        all_plugins_map = {p.name: p for p in all_plugins_list}

                        for plugin in all_plugins_map.values():
                            if hasattr(plugin, "get_tool_definitions"):
                                for tool_def in plugin.get_tool_definitions():
                                    function = tool_def.get("function", {})
                                    func_name = function.get("name")
                                    params_schema = function.get("parameters")
                                    if func_name and params_schema:
                                        fields = {}
                                        required_fields = params_schema.get("required", [])
                                        for prop_name, prop_def in params_schema.get(
                                            "properties", {}
                                        ).items():
                                            field_type = {
                                                "string": str,
                                                "integer": int,
                                                "number": float,
                                                "boolean": bool,
                                                "array": list,
                                            }.get(prop_def.get("type"), str)
                                            desc = prop_def.get("description")
                                            default_value = prop_def.get("default")
                                            
                                            # Use Field(...) for required, Field(default=...) for optional
                                            if prop_name in required_fields:
                                                fields[prop_name] = (
                                                    field_type,
                                                    Field(..., description=desc),
                                                )
                                            else:
                                                fields[prop_name] = (
                                                    field_type,
                                                    Field(default=default_value, description=desc),
                                                )

                                        validation_model = create_model(
                                            f"{func_name}ArgsModel", **fields
                                        )
                                        tool_schemas[func_name] = validation_model

                        step_results = []
                        step_outputs: Dict[int, Any] = {}
                        plan_failed = False
                        for step_index, step in enumerate(plan):
                            tool_name = step.get("tool_name")
                            method_name = step.get("method_name")
                            arguments = step.get("arguments", {})

                            # --- Resolve chained results (supports both old and new syntax) ---
                            for arg_name, arg_value in list(arguments.items()):
                                # New syntax: ${step_N.field} or ${step_N}
                                if isinstance(arg_value, str) and "${step_" in arg_value:
                                    import re
                                    # Match ${step_N.field} or ${step_N}
                                    pattern = r'\$\{step_(\d+)(?:\.(\w+))?\}'
                                    matches = re.findall(pattern, arg_value)
                                    
                                    replacement = arg_value
                                    for match in matches:
                                        source_step_index = int(match[0])
                                        field_name = match[1] if match[1] else None
                                        
                                        if source_step_index in step_outputs:
                                            output = step_outputs[source_step_index]
                                            
                                            # Extract specific field if requested
                                            if field_name:
                                                if hasattr(output, field_name):
                                                    value = getattr(output, field_name)
                                                elif isinstance(output, dict) and field_name in output:
                                                    value = output[field_name]
                                                else:
                                                    context.logger.warning(
                                                        f"Field '{field_name}' not found in step {source_step_index} output",
                                                        extra={"plugin_name": "Kernel"},
                                                    )
                                                    value = str(output)
                                            else:
                                                value = str(output)
                                            
                                            # Replace in the argument value
                                            placeholder = f"${{step_{source_step_index}" + (f".{field_name}" if field_name else "") + "}"
                                            replacement = replacement.replace(placeholder, str(value))
                                        else:
                                            context.logger.error(
                                                f"Could not find result for step {source_step_index}",
                                                extra={"plugin_name": "Kernel"},
                                            )
                                    
                                    arguments[arg_name] = replacement
                                
                                # Old syntax: $result.step_N (keep for backward compatibility)
                                elif isinstance(arg_value, str) and arg_value.startswith(
                                    "$result.step_"
                                ):
                                    try:
                                        source_step_index = int(arg_value.split("_")[-1])
                                        if source_step_index in step_outputs:
                                            arguments[arg_name] = str(
                                                step_outputs[source_step_index]
                                            )
                                        else:
                                            context.logger.error(
                                                f"Could not find result for step "
                                                f"{source_step_index} in outputs.",
                                                extra={"plugin_name": "Kernel"},
                                            )
                                    except (IndexError, ValueError) as e:
                                        context.logger.error(
                                            f"Error parsing chained result '{arg_value}': {e}",
                                            extra={"plugin_name": "Kernel"},
                                        )

                            validated_args = None
                            max_attempts = 3

                            for attempt in range(max_attempts):
                                try:
                                    validation_model = tool_schemas.get(method_name)
                                    if not validation_model:
                                        msg = (
                                            f"No validation schema found for method "
                                            f"'{method_name}'."
                                        )
                                        raise ValueError(msg)

                                    current_args = arguments
                                    if isinstance(current_args, str):
                                        try:
                                            current_args = json.loads(current_args)
                                        except json.JSONDecodeError:
                                            msg = (
                                                f"Arguments are a non-JSON string: "
                                                f"{current_args}"
                                            )
                                            raise ValueError(msg)

                                    validated_args = validation_model(**current_args).model_dump()
                                    log_message = (
                                        f"SECOND-PHASE LOG: Validated plan step "
                                        f"{step_index + 1}: "
                                        f"{tool_name}.{method_name}({validated_args})"
                                    )
                                    context.logger.info(
                                        log_message, extra={"plugin_name": tool_name}
                                    )
                                    break  # Success

                                except (ValidationError, ValueError) as e:
                                    log_message = (
                                        f"Validation failed for step {step_index + 1} "
                                        f"(Attempt {attempt + 1}/{max_attempts}): {e}"
                                    )
                                    context.logger.warning(
                                        log_message, extra={"plugin_name": "Kernel"}
                                    )
                                    if attempt + 1 == max_attempts:
                                        error_message = (
                                            f"Plan failed at step {step_index + 1} "
                                            f"after {max_attempts} attempts. "
                                            f"Final error: {e}"
                                        )
                                        context.logger.error(
                                            error_message, extra={"plugin_name": "Kernel"}
                                        )
                                        step_results.append(error_message)
                                        plan_failed = True
                                        break

                                    if not llm_tool:
                                        error_message = "Cannot attempt repair: LLMTool not found."
                                        context.logger.error(
                                            error_message, extra={"plugin_name": "Kernel"}
                                        )
                                        step_results.append(error_message)
                                        plan_failed = True
                                        break

                                    # Convert step_outputs to JSON-serializable format
                                    serializable_outputs = []
                                    for output in step_outputs:
                                        if hasattr(output, 'model_dump'):
                                            serializable_outputs.append(output.model_dump())
                                        elif isinstance(output, (str, int, float, bool, type(None))):
                                            serializable_outputs.append(output)
                                        else:
                                            serializable_outputs.append(str(output))
                                    
                                    corrupted_json_data = {
                                        "tool_name": tool_name,
                                        "method_name": method_name,
                                        "arguments": arguments,
                                        "error": str(e),
                                        "user_input": context.user_input,
                                        "previous_steps": serializable_outputs,
                                    }
                                    
                                    # Get function schema for repair
                                    function_schema = validation_model.model_json_schema() if hasattr(validation_model, 'model_json_schema') else {}
                                    
                                    repair_prompt = self.json_repair_prompt_template.format(
                                        user_input=context.user_input or "",
                                        tool_name=tool_name,
                                        method_name=method_name,
                                        error=str(e),
                                        function_schema=json.dumps(function_schema, indent=2),
                                        previous_steps=json.dumps(serializable_outputs, indent=2),
                                        arguments=json.dumps(arguments, indent=2)
                                    )

                                    repair_context = await llm_tool.execute(
                                        context=SharedContext(
                                            session_id=context.session_id,
                                            current_state="EXECUTING",
                                            logger=context.logger,
                                            user_input=repair_prompt,
                                            history=[{"role": "user", "content": repair_prompt}],
                                        )
                                    )

                                    repaired_args = repair_context.payload.get("llm_response")
                                    if isinstance(repaired_args, list) and repaired_args:
                                        arguments = repaired_args[0].get("arguments", {})
                                    elif isinstance(repaired_args, dict):
                                        arguments = repaired_args.get("arguments", {})

                                    context.logger.info(
                                        f"Received repaired arguments for step "
                                        f"{step_index + 1}: {arguments}",
                                        extra={"plugin_name": "Kernel"},
                                    )

                            if plan_failed or validated_args is None:
                                execution_summary = f"Plan failed at step {step_index + 1}."
                                break

                            tool = all_plugins_map.get(tool_name)
                            method = getattr(tool, method_name, None) if tool else None
                            if method:
                                try:
                                    # --- Context Injection & History Propagation ---
                                    import inspect

                                    sig = inspect.signature(method)
                                    call_args = validated_args.copy()

                                    if "context" in sig.parameters:
                                        # Create a new context for this specific step
                                        step_history = context.history[:]
                                        for i in range(1, step_index + 1):
                                            if i in step_outputs:
                                                step_history.append(
                                                    {
                                                        "role": "assistant",
                                                        "content": f"Output of step {i}: "
                                                        f"{step_outputs[i]}",
                                                    }
                                                )

                                        step_context = SharedContext(
                                            session_id=context.session_id,
                                            current_state="EXECUTING",
                                            logger=context.logger,
                                            history=step_history,
                                            user_input=str(call_args),
                                        )
                                        call_args["context"] = step_context

                                    step_result = (
                                        await method(**call_args)
                                        if asyncio.iscoroutinefunction(method)
                                        else method(**call_args)
                                    )

                                    # --- Result Handling & Chaining ---
                                    output_for_chaining = ""
                                    if isinstance(step_result, SharedContext):
                                        context.payload.update(step_result.payload)
                                        output_for_chaining = step_result.payload.get(
                                            "llm_response", ""
                                        )
                                        step_results.append(str(output_for_chaining))
                                    else:
                                        output_for_chaining = step_result
                                        step_results.append(str(step_result))

                                    step_outputs[step_index + 1] = output_for_chaining
                                    
                                    # Save step completion to memory for recovery
                                    if self.memory:
                                        try:
                                            # Create a temporary context for memory storage
                                            mem_context = SharedContext(
                                                session_id=context.session_id,
                                                current_state="EXECUTING",
                                                logger=context.logger,
                                                user_input=f"[STEP {step_index + 1}] {tool_name}.{method_name}",
                                                history=context.history
                                            )
                                            mem_context.payload["llm_response"] = (
                                                f"Step {step_index + 1} completed: {tool_name}.{method_name}\n"
                                                f"Arguments: {validated_args}\n"
                                                f"Result: {str(output_for_chaining)[:500]}\n"
                                                f"Timestamp: {datetime.now().isoformat()}"
                                            )
                                            await self.memory.execute(mem_context)
                                        except Exception as mem_err:
                                            context.logger.warning(
                                                f"Failed to save step to memory: {mem_err}",
                                                extra={"plugin_name": "Kernel"}
                                            )
                                    
                                    context.logger.info(
                                        f"Step '{method_name}' executed. "
                                        f"Result: {step_result}",
                                        extra={"plugin_name": tool_name},
                                    )
                                except Exception as exec_err:
                                    error_message = (
                                        f"Error executing {tool_name}.{method_name}: "
                                        f"{exec_err}"
                                    )
                                    context.logger.error(
                                        error_message,
                                        exc_info=True,
                                        extra={"plugin_name": tool_name},
                                    )
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
                                context.logger.error(
                                    error_message, extra={"plugin_name": "Kernel"}
                                )
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
                            context.logger.info(
                                "No plan generated, attempting direct LLM response.",
                                extra={"plugin_name": "Kernel"},
                            )
                            context = await llm_tool.execute(context=context)
                            execution_summary = context.payload.get(
                                "llm_response", "Input received, no plan formed."
                            )
                        else:
                            execution_summary = (
                                "Input received, but no planner or LLM tool is configured."
                            )
                            context.logger.warning(
                                "No plan and no LLM tool found for direct response.",
                                extra={"plugin_name": "Kernel"},
                            )

                    # 4. RESPONDING PHASE
                    context.current_state = "RESPONDING"
                    context.payload["final_response"] = execution_summary
                    context.logger.info(
                        f"Final response: {execution_summary}",
                        extra={"plugin_name": "Kernel"},
                    )
                    context.history.append({"role": "assistant", "content": execution_summary})

                    response_callback = context.payload.get("_response_callback")
                    if response_callback:
                        try:
                            if asyncio.iscoroutinefunction(response_callback):
                                await response_callback(execution_summary)
                            else:
                                response_callback(execution_summary)
                        except Exception as cb_err:
                            context.logger.error(
                                f"Error in response callback: {cb_err}",
                                exc_info=True,
                                extra={"plugin_name": "Kernel"},
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
                context.logger.info(
                    "Consciousness loop cancelled.", extra={"plugin_name": "Kernel"}
                )
                self.is_running = False
                break
            except Exception as e:
                context.logger.error(
                    f"Unexpected error in consciousness loop: {e}",
                    exc_info=True,
                    extra={"plugin_name": "Kernel"},
                )
                # Publish SYSTEM_ERROR event if event-driven
                if self.use_event_driven:
                    from core.events import Event, EventType, EventPriority
                    self.event_bus.publish(Event(
                        event_type=EventType.SYSTEM_ERROR,
                        source="kernel",
                        priority=EventPriority.CRITICAL,
                        data={"error": str(e), "session_id": session_id}
                    ))
                await asyncio.sleep(5)

        context.logger.info("Consciousness loop finished.", extra={"plugin_name": "Kernel"})
        
        # NEW: Graceful shutdown of event-driven components
        await self._shutdown_event_system(context, session_id)
    
    async def _shutdown_event_system(self, context: SharedContext, session_id: str):
        """
        Gracefully shutdown event-driven components.
        
        Args:
            context: Shared context
            session_id: Current session ID
        """
        if self.use_event_driven and self.event_bus:
            from core.events import Event, EventType, EventPriority
            
            # Publish shutdown event
            self.event_bus.publish(Event(
                event_type=EventType.SYSTEM_SHUTDOWN,
                source="kernel",
                priority=EventPriority.CRITICAL,
                data={"session_id": session_id}
            ))
            
            # Wait briefly for events to process
            await asyncio.sleep(0.5)
            
            # Stop task queue first
            if self.task_queue:
                await self.task_queue.stop()
                context.logger.info(
                    "Task queue stopped gracefully",
                    extra={"plugin_name": "Kernel"}
                )
            
            # Stop event bus
            await self.event_bus.stop()
            context.logger.info(
                "Event bus stopped gracefully",
                extra={"plugin_name": "Kernel"}
            )

    async def process_single_input(self, context: SharedContext) -> str:
        """
        Process single input without interface plugins.
        Used for CLI/scripted interactions (--once mode).
        
        Args:
            context: Context with user_input already set
            
        Returns:
            Response string
        """
        logger.info(f"[Kernel] Processing single input: {context.user_input}")
        
        # Skip LISTENING phase (already have input)
        # Go straight to: PLANNING → EXECUTING → RESPONDING
        
        # 1. PLANNING PHASE
        context.current_state = "PLANNING"
        context.history.append({"role": "user", "content": context.user_input})
        
        # --- Cognitive Task Routing ---
        router = self.all_plugins_map.get("cognitive_task_router")
        if router:
            try:
                context = await router.execute(context=context)
                logger.info("Cognitive Task Router executed successfully.")
            except Exception as e:
                logger.error(f"Error executing Cognitive Task Router: {e}")
        
        # --- Planning ---
        planner = self.all_plugins_map.get("cognitive_planner")
        plan = []
        if planner:
            context = await planner.execute(context)
            plan = context.payload.get("plan", [])
            if not isinstance(plan, list):
                logger.error(f"Planner returned invalid plan: {plan}. Defaulting to empty.")
                plan = []
        else:
            logger.warning("Cognitive planner plugin not found.")
        
        # 2. EXECUTING PHASE
        context.current_state = "EXECUTING"
        execution_result = {"success": False, "output": ""}
        
        if plan:
            logger.info(f"Executing plan with {len(plan)} steps")
            # Execute plan steps (simplified - just get LLM response for now)
            llm_tool = self.all_plugins_map.get("tool_llm")
            if llm_tool:
                try:
                    # Get LLM to respond directly for simplicity
                    llm_context = await llm_tool.execute(context=context)
                    response_text = llm_context.payload.get("llm_response", "No response generated")
                    execution_result = {"success": True, "output": response_text}
                except Exception as e:
                    execution_result = {"success": False, "error": str(e)}
            else:
                execution_result = {"success": False, "error": "No LLM tool found"}
        else:
            execution_result = {"success": False, "error": "No plan generated"}
        
        # 3. RESPONDING
        context.current_state = "RESPONDING"
        response = self._generate_response(context, execution_result)
        
        logger.info(f"[Kernel] Single input processed, response ready")
        return response
    
    def _generate_response(self, context: SharedContext, execution_result: dict) -> str:
        """Generate user-facing response from execution result."""
        if execution_result.get("success"):
            return execution_result.get("output", "Task completed successfully.")
        else:
            return f"Error: {execution_result.get('error', 'Unknown error')}"

    def start(self):
        """Starts the main consciousness loop."""
        try:
            asyncio.run(self.consciousness_loop())
        except KeyboardInterrupt:
            logger.info(
                "Application terminated by user (Ctrl+C).",
                extra={"plugin_name": "Kernel"},
            )
