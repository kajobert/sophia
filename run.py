import asyncio
import sys
import os
import argparse
from dotenv import load_dotenv
from core.kernel import Kernel
from plugins.base_plugin import PluginType


async def _load_scifi_interface(kernel, ui_style: str):
    """Load sci-fi terminal interface plugin and REMOVE classic terminal."""
    try:
        if ui_style == "matrix":
            from plugins.interface_terminal_matrix import InterfaceTerminalMatrix
            interface = InterfaceTerminalMatrix()
            print("🟢 Loading Matrix interface... 'Follow the white rabbit!' 🐰")
        elif ui_style == "startrek":
            from plugins.interface_terminal_startrek import InterfaceTerminalStarTrek
            interface = InterfaceTerminalStarTrek()
            print("🟡 Loading Star Trek LCARS interface... 'Make it so!' 🖖")
        elif ui_style == "cyberpunk":
            from plugins.interface_terminal_scifi import InterfaceTerminalSciFi
            interface = InterfaceTerminalSciFi()
            print("🌈 Loading Cyberpunk interface... Maximum WOW! ⚡")
        else:
            return None  # Classic mode, use default
        
        # CRITICAL: Remove ALL existing interface plugins first!
        kernel.plugin_manager._plugins[PluginType.INTERFACE] = []
        
        # Setup and register ONLY our sci-fi interface
        interface.setup({})
        kernel.plugin_manager._plugins[PluginType.INTERFACE].append(interface)
        kernel.all_plugins_map[interface.name] = interface
        
        print(f"✅ {interface.name} ready!\n")
        
        return interface  # Return interface for logging hookup
        
    except Exception as e:
        print(f"⚠️  Warning: Could not load {ui_style} interface: {e}")
        print("   Falling back to classic terminal...")
        return None


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
        "--ui",
        choices=["matrix", "startrek", "cyberpunk", "classic"],
        default=None,
        help="Choose sci-fi terminal UI style (matrix, startrek, cyberpunk, or classic)"
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="Non-interactive input for single-run mode"
    )
    args = parser.parse_args()
    
    # Determine UI style (CLI arg > ENV var > default cyberpunk)
    ui_style = args.ui or os.getenv("SOPHIA_UI_STYLE", "cyberpunk")
    
    print("Starting Sophia's kernel...")
    if args.use_event_driven:
        print("🚀 Event-driven architecture ENABLED (Phase 1)")
    
    # Print UI style
    ui_icons = {
        "matrix": "🟢 MATRIX",
        "startrek": "🟡 STAR TREK LCARS",
        "cyberpunk": "🌈 CYBERPUNK",
        "classic": "⚪ CLASSIC"
    }
    print(f"🎨 UI Style: {ui_icons.get(ui_style, ui_style.upper())}")
    
    kernel = Kernel(use_event_driven=args.use_event_driven)
    
    # IMPORTANT: Initialize kernel FIRST to load all plugins
    await kernel.initialize()
    
    # THEN replace interface plugin if sci-fi mode requested
    if ui_style != "classic":
        scifi_interface = await _load_scifi_interface(kernel, ui_style)
        
        # Install sci-fi logging handler to redirect logs to colorful UI
        if scifi_interface:
            from core.scifi_logging import install_scifi_logging
            install_scifi_logging(scifi_interface)
            print(f"✨ Sci-fi logging enabled - all output now in {ui_style.upper()} style!")

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
    # Suppress warnings for clean UI
    import warnings
    warnings.filterwarnings("ignore")
    
    # Suppress langfuse startup messages
    os.environ["LANGFUSE_ENABLED"] = "false"
    
    asyncio.run(main())
