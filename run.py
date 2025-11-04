import asyncio
import sys
import os
import time
import logging
import argparse

# ⚡ CRITICAL: Load .env BEFORE any plugin imports!
# This ensures JULES_API_KEY and other env vars are available when plugins initialize
from dotenv import load_dotenv

load_dotenv()

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

        # Register ONLY our sci-fi interface (setup already called by kernel)
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
    # Suppress warnings FIRST (before any imports that might warn)
    import warnings

    warnings.filterwarnings("ignore")
    os.environ["LANGFUSE_ENABLED"] = "false"

    check_venv()
    # .env already loaded at module level (before imports)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Sophia AI Assistant")
    parser.add_argument(
        "--use-event-driven",
        action="store_true",
        help="Enable event-driven architecture (Phase 1 - EXPERIMENTAL)",
    )
    parser.add_argument(
        "--ui",
        choices=["matrix", "startrek", "cyberpunk", "classic"],
        default=None,
        help="Choose sci-fi terminal UI style (matrix, startrek, cyberpunk, or classic)",
    )
    parser.add_argument(
        "--no-webui",
        action="store_true",
        help="Disable Web UI (terminal-only mode for faster startup and simple interaction)",
    )
    parser.add_argument(
        "--once", type=str, help="Single-run mode: process one input and exit (fast, no UI)"
    )
    parser.add_argument("input", nargs="*", help="Non-interactive input for single-run mode")
    args = parser.parse_args()

    # Determine UI style (CLI arg > ENV var > default CLASSIC for stability)
    ui_style = args.ui or os.getenv("SOPHIA_UI_STYLE", "classic")

    print("Starting Sophia's kernel...")
    if args.use_event_driven:
        print("🚀 Event-driven architecture ENABLED (Phase 1)")

    # Print UI style
    ui_icons = {
        "matrix": "🟢 MATRIX",
        "startrek": "🟡 STAR TREK LCARS",
        "cyberpunk": "🌈 CYBERPUNK",
        "classic": "⚪ CLASSIC",
    }
    print(f"🎨 UI Style: {ui_icons.get(ui_style, ui_style.upper())}")

    kernel = Kernel(use_event_driven=args.use_event_driven)

    # IMPORTANT: Initialize kernel to load all plugins
    await kernel.initialize()

    # ADAPTIVE UI: Remove interface plugins AFTER init in single-run mode (Gemini's optimization)
    if args.once or args.input:
        # Clear interfaces to avoid any UI overhead
        removed_count = len(kernel.plugin_manager._plugins[PluginType.INTERFACE])
        kernel.plugin_manager._plugins[PluginType.INTERFACE] = []
        print(f"🎯 Single-run mode: {removed_count} interface plugins disabled for speed")
    # DISABLE WebUI if --no-webui flag is set
    elif args.no_webui:
        # Remove only WebUI, keep terminal
        webui_removed = False
        kernel.plugin_manager._plugins[PluginType.INTERFACE] = [
            p
            for p in kernel.plugin_manager._plugins[PluginType.INTERFACE]
            if p.name != "interface_webui"
        ]
        print(f"🚫 Web UI disabled - terminal-only mode")
    # THEN replace interface plugin if sci-fi mode requested (interactive only)
    elif ui_style != "classic":
        scifi_interface = await _load_scifi_interface(kernel, ui_style)

        # Install sci-fi logging handler to redirect logs to colorful UI
        if scifi_interface:
            from core.scifi_logging import install_scifi_logging

            install_scifi_logging(scifi_interface)
            print(f"✨ Sci-fi logging enabled - all output now in {ui_style.upper()} style!")

    # SINGLE-RUN MODE: Fast processing without UI
    if args.once or args.input:
        single_input = args.once if args.once else " ".join(args.input)
        print(f"🎯 Single-run mode activated: '{single_input}'")

        from core.context import SharedContext

        # Create minimal logger for single-run
        session_id = f"single-run-{int(time.time())}"
        session_logger = logging.getLogger(f"sophia.{session_id}")

        context = SharedContext(
            user_input=single_input,
            session_id=session_id,
            current_state="SINGLE_RUN",
            logger=session_logger,
        )

        # Process single input with timeout
        try:
            response = await asyncio.wait_for(
                kernel.process_single_input(context),
                timeout=30.0,  # Increased from 5s - Jules operations can take time
            )
            print(f"\n✅ Sophia: {response}\n")
            sys.exit(0)
        except asyncio.TimeoutError:
            print("\n❌ Error: Response timeout (>30s)\n")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    # INTERACTIVE MODE: Normal operation with UI
    else:
        # Start normal interactive loop (no need to call prompt() - already handled)
        await kernel.consciousness_loop()

    print("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    asyncio.run(main())
