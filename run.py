import asyncio
import sys
from core.kernel import Kernel
from plugins.base_plugin import PluginType


def check_venv():
    """Check if the application is running in a virtual environment."""
    if sys.prefix == sys.base_prefix:
        print("---")
        print(
            "ERROR: It looks like you are not running this application in a virtual environment."
        )
        print("Please activate the virtual environment first.")
        print("Example: source .venv/bin/activate")
        print("---")
        sys.exit(1)



async def main():
    """The main entry point of the application."""
    check_venv()
    print("Starting Sophia's kernel...")
    kernel = Kernel()
    await kernel.initialize()

    # Display the initial prompt for the terminal interface, if available.
    terminal_plugins = kernel.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
    for plugin in terminal_plugins:
        if plugin.name == "interface_terminal" and hasattr(plugin, "prompt"):
            plugin.prompt()

    await kernel.consciousness_loop()
    print("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    asyncio.run(main())
