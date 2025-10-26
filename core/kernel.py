import asyncio
import logging
import yaml
from pathlib import Path
from core.context import SharedContext
from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType

# Basic logging setup for Kernel execution
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
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
        self._setup_plugins()

    def _setup_plugins(self):
        """Loads plugin configurations, instantiates all plugins, and then calls their setup methods."""
        # Load YAML config (as before)
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            logger.warning("Configuration file 'config/settings.yaml' not found.")
            config = {}
        else:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

        plugin_configs = config.get("plugins", {})

        # 1. Create a map of all instantiated plugins
        all_plugins_list = [
            plugin
            for plugin_list in self.plugin_manager._plugins.values()
            for plugin in plugin_list
        ]
        all_plugins_map = {p.name: p for p in all_plugins_list}

        # 2. Now, iterate again and call setup on each plugin
        for plugin in all_plugins_list:
            # Start with the specific config from the YAML file
            specific_config = plugin_configs.get(plugin.name, {})

            # Add all other plugins to the config for dependency injection
            # This allows any plugin to access any other plugin if needed
            final_config = {
                "plugin_manager": self.plugin_manager,
                **all_plugins_map,
                **specific_config # The specific config can override the general map
            }

            try:
                plugin.setup(final_config)
                logger.info(f"Successfully set up plugin '{plugin.name}'.")
            except Exception as e:
                logger.error(f"Error setting up plugin '{plugin.name}': {e}", exc_info=True)

    async def consciousness_loop(self):
        """The main, infinite loop that keeps Sophia "conscious"."""
        self.is_running = True
        session_id = "persistent_session_01"  # Using persistent session for now
        logger.info(f"New session started with ID: {session_id}")

        memory_plugins = self.plugin_manager.get_plugins_by_type(PluginType.MEMORY)
        if memory_plugins:
            initial_history = memory_plugins[0].get_history(session_id)
        else:
            initial_history = []

        context = SharedContext(
            session_id=session_id,
            current_state="INITIALIZING",
            logger=logging.getLogger(f"session-{session_id[:8]}"),
            history=initial_history,
        )

        all_plugins_list = [p for pt in PluginType for p in self.plugin_manager.get_plugins_by_type(pt)]
        all_plugins_map = {p.name: p for p in all_plugins_list}
        while self.is_running:
            try:
                # 1. LISTENING PHASE
                context.current_state = "LISTENING"
                interface_plugins = self.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
                if not interface_plugins:
                    logger.warning("No INTERFACE plugins found. Waiting...")
                    await asyncio.sleep(5)
                    continue

                input_tasks = [asyncio.create_task(p.execute(context)) for p in interface_plugins]
                done, pending = await asyncio.wait(
                    input_tasks, return_when=asyncio.FIRST_COMPLETED
                )

                for task in pending:
                    task.cancel()

                if done:
                    context = done.pop().result()

                if context.user_input:
                    logger.info(f"User input received: '{context.user_input}'")
                    context.history.append({"role": "user", "content": context.user_input})

                    # 2. PLANNING PHASE (NEW)
                    context.current_state = "PLANNING"
                    cognitive_plugins = self.plugin_manager.get_plugins_by_type(PluginType.COGNITIVE)
                    for plugin in cognitive_plugins:
                        if plugin.name == "cognitive_planner":
                            context = await plugin.execute(context)
                    plan = context.payload.get("plan", [])
                    final_result = ""

                    # 3. EXECUTING PHASE (NEW)
                    context.current_state = "EXECUTING"
                    if plan:
                        logger.info(f"Executing plan: {plan}")
                        for step in plan:
                            tool_name = step.get("tool_name")
                            method_name = step.get("method_name")
                            arguments = step.get("arguments", {})
                            tool = all_plugins_map.get(tool_name)
                            if tool and hasattr(tool, method_name):
                                method = getattr(tool, method_name)
                                if asyncio.iscoroutinefunction(method):
                                    result = await method(**arguments)
                                else:
                                    result = method(**arguments)
                                final_result += str(result) + "\n"
                                logger.info(f"Step '{method_name}' executed. Result: {result}")
                            else:
                                error_message = f"Error: Tool '{tool_name}' or method '{method_name}' not found."
                                final_result += error_message
                                logger.error(error_message)
                                break  # Stop execution on error
                    else:
                        final_result = "I was unable to create a plan to fulfill your request."

                    # 4. RESPONDING PHASE
                    print(f">>> Sophia: {final_result.strip()}")
                    context.history.append({"role": "assistant", "content": final_result.strip()})
                    response_callback = context.payload.get("_response_callback")
                    if callable(response_callback):
                        context.logger.info("Found a response callback. Sending response...")
                        await response_callback(final_result.strip())

                    # 5. MEMORIZING PHASE
                    context.current_state = "MEMORIZING"
                    memory_plugins = self.plugin_manager.get_plugins_by_type(PluginType.MEMORY)
                    for plugin in memory_plugins:
                        context = await plugin.execute(context)

                    # Cleanup for next cycle
                    context.user_input = None
                    context.payload = {}

                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                self.is_running = False
                logger.info("Consciousness loop was cancelled.")
            except Exception as e:
                logger.error(f"Unexpected error in consciousness loop: {e}", exc_info=True)
                self.is_running = False

    def start(self):
        """Starts the main consciousness loop."""
        try:
            asyncio.run(self.consciousness_loop())
        except KeyboardInterrupt:
            logger.info("Application terminated by user (Ctrl+C).")
