import asyncio
import sys
from core.kernel import Kernel
from plugins.base_plugin import PluginType
from core.logger import logger


def check_venv():
    """Check if the application is running in a virtual environment."""
    if sys.prefix == sys.base_prefix:
        logger.error("---")
        logger.error(
            "It looks like you are not running this application in a virtual environment."
        )
        logger.error("Please activate the virtual environment first.")
        logger.error("Example: source .venv/bin/activate")
        logger.error("---")
        sys.exit(1)


async def main():
    """The main entry point of the application."""
    check_venv()
    logger.info("Starting Sophia's kernel...")
    kernel = Kernel()
    await kernel.initialize()

    # Display the initial prompt for the terminal interface, if available.
    terminal_plugins = kernel.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
    for plugin in terminal_plugins:
        if plugin.name == "interface_terminal" and hasattr(plugin, "prompt"):
            plugin.prompt()

    await kernel.consciousness_loop()
    logger.info("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Kernel interrupted by user. Shutting down.")
    except Exception as e:
        logger.critical(f"A critical error occurred: {e}", exc_info=True)
        sys.exit(1)
