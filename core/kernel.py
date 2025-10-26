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
        """Loads plugin configurations and calls their setup methods."""
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            logger.warning("Configuration file 'config/settings.yaml' not found.")
            config = {}
        else:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

        plugin_configs = config.get("plugins", {})

        all_plugins = [
            plugin
            for plugin_list in self.plugin_manager._plugins.values()
            for plugin in plugin_list
        ]

        for plugin in all_plugins:
            plugin_config = plugin_configs.get(plugin.name, {})
            # Add the plugin_manager to the config
            plugin_config["plugin_manager"] = self.plugin_manager
            try:
                plugin.setup(plugin_config)
                logger.info(f"Successfully set up plugin '{plugin.name}'.")
            except Exception as e:
                logger.error(f"Error setting up plugin '{plugin.name}': {e}", exc_info=True)

    async def consciousness_loop(self):
        """The main, infinite loop that keeps Sophia "conscious"."""
        self.is_running = True
        session_id = str(uuid.uuid4()) # --- PLUGIN SETUP PHASE ---
        all_plugins_list = [p for pt in PluginType for p in self.plugin_manager.get_plugins_by_type(pt)]
        all_plugins_map = {p.name: p for p in all_plugins_list}
        for plugin in all_plugins_list:
            plugin_config = {
                "plugin_manager": self.plugin_manager,
                **all_plugins_map # Pass all tools to all plugins for now
            }
            plugin.setup(plugin_config)
        logger.info(f"All {len(all_plugins_list)} plugins have been configured.")
        # ... (rest of the setup phase as before)
        context = SharedContext(
            session_id=session_id,
            current_state="INITIALIZING",
            logger=logging.getLogger(f"session-{session_id[:8]}"),
            history=[]
        )
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
                try:
                    done, pending = await asyncio.wait_for(
                        asyncio.wait(input_tasks, return_when=asyncio.FIRST_COMPLETED),
                        timeout=1.0,
                    )
                    for task in pending:
                        task.cancel()
                    if done:
                        context = done.pop().result()
                except asyncio.TimeoutError:
                    for task in input_tasks:
                        task.cancel()
                    context.user_input = None
                if context.user_input:
                    logger.info(f"User input received: '{context.user_input}'")
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
                                # This is a simplification; real implementation would handle async/sync methods
                                if asyncio.iscoroutinefunction(method):
                                    final_result = await method(**arguments)
                                else:
                                    final_result = method(**arguments)
                                logger.info(f"Step '{method_name}' executed. Result: {final_result}")
                            else:
                                final_result = f"Error: Tool '{tool_name}' or method '{method_name}' not found."
                                logger.error(final_result)
                                break # Stop execution on error
                    else:
                        final_result = "I was unable to create a plan to fulfill your request."
                    # 4. RESPONDING PHASE (remains the same, but uses final_result)
                    # ...
                    # 5. MEMORIZING PHASE (remains the same)
                    # ...
            except Exception as e:
                logger.error(f"Unexpected error in consciousness loop: {e}", exc_info=True)
                self.is_running = False

    def start(self):
        """Starts the main consciousness loop."""
        try:
            asyncio.run(self.consciousness_loop())
        except KeyboardInterrupt:
            logger.info("Application terminated by user (Ctrl+C).")
