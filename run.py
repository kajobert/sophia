import asyncio
import sys
import argparse
from dotenv import load_dotenv
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
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Sophia AI Assistant")
    parser.add_argument(
        "--use-event-driven",
        action="store_true",
        help="Enable event-driven architecture (Phase 1 - EXPERIMENTAL)"
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="Non-interactive input for single-run mode"
    )
    args = parser.parse_args()
    
    print("Starting Sophia's kernel...")
    if args.use_event_driven:
        print("🚀 Event-driven architecture ENABLED (Phase 1)")
    
    kernel = Kernel(use_event_driven=args.use_event_driven)
    await kernel.initialize()

    # Zjistíme, jestli byl zadán vstup jako argument
    if args.input:
        user_input = " ".join(args.input)
        print(f"Running in non-interactive mode with input: '{user_input}'")
        await kernel.consciousness_loop(single_run_input=user_input)
    else:
        # Spustíme normální interaktivní smyčku
        terminal_plugins = kernel.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
        for plugin in terminal_plugins:
            if plugin.name == "interface_terminal" and hasattr(plugin, "prompt"):
                plugin.prompt()
        await kernel.consciousness_loop()

    print("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    asyncio.run(main())
