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
            try:
                plugin.setup(plugin_config)
                logger.info(f"Successfully set up plugin '{plugin.name}'.")
            except Exception as e:
                logger.error(f"Error setting up plugin '{plugin.name}': {e}", exc_info=True)

    async def consciousness_loop(self):
        self.is_running = True
        session_id = "persistent_session_01"
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

                # 2. THINKING PHASE
                context.current_state = "THINKING"
                tool_plugins = self.plugin_manager.get_plugins_by_type(PluginType.TOOL)
                for plugin in tool_plugins:
                    context = await plugin.execute(context)
                llm_response = context.payload.get("llm_response", "I have no response.")
                context.history.append({"role": "assistant", "content": llm_response})

                # 4. RESPONDING PHASE
                # The terminal gets the response by default.
                print(f">>> Sophia: {llm_response}")
                # Check if the context contains a special callback for responding.
                # This allows any plugin to request a direct response.
                response_callback = context.payload.get("_response_callback")
                if callable(response_callback):
                    context.logger.info("Found a response callback. Sending response...")
                    await response_callback(llm_response)

                # 3. MEMORIZING PHASE
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
