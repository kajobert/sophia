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
from pathlib import Path
import json


async def _check_pending_upgrade(kernel):
    """
    Check for pending autonomous upgrade validation (Phase 3.7).
    
    If upgrade_state.json exists, this means:
    1. SOPHIA deployed code change in previous session
    2. Restarted to apply changes
    3. Need to validate upgrade now
    
    Workflow:
    - Load upgrade_state.json
    - Call cognitive_self_tuning._validate_upgrade()
    - If validation passes: finalize upgrade
    - If validation fails: rollback deployment
    """
    upgrade_state_file = Path(".data/upgrade_state.json")
    
    if not upgrade_state_file.exists():
        return  # No pending upgrade
    
    try:
        print("🔄 Pending autonomous upgrade detected!")
        
        with open(upgrade_state_file, 'r') as f:
            upgrade_state = json.load(f)
        
        hypothesis_id = upgrade_state.get('hypothesis_id')
        target_file = upgrade_state.get('target_file')
        
        print(f"📝 Hypothesis: {hypothesis_id}")
        print(f"📝 Modified file: {target_file}")
        print(f"🧪 Running upgrade validation...")
        
        # Get cognitive_self_tuning plugin
        self_tuning = kernel.all_plugins_map.get('cognitive_self_tuning')
        
        if not self_tuning:
            print("❌ ERROR: cognitive_self_tuning plugin not found!")
            print("⚠️  Cannot validate upgrade, keeping current state")
            return
        
        # Increment attempt counter
        upgrade_state['validation_attempts'] = upgrade_state.get('validation_attempts', 0) + 1
        
        # Check max attempts
        if upgrade_state['validation_attempts'] > upgrade_state.get('max_attempts', 3):
            print(f"❌ Max validation attempts exceeded ({upgrade_state['max_attempts']})")
            print(f"⚠️  Triggering rollback...")
            await self_tuning._rollback_deployment(upgrade_state)
            upgrade_state_file.unlink()  # Clean up
            return
        
        # Run validation
        validation_result = await self_tuning._validate_upgrade(upgrade_state)
        
        if validation_result:
            print("✅ Upgrade validation PASSED!")
            print("✅ Upgrade finalized, cleaning up state...")
            
            # Clean up upgrade state
            upgrade_state_file.unlink()
            
            # Clean up backup file
            backup_file = Path(upgrade_state.get('backup_file'))
            if backup_file.exists():
                backup_file.unlink()
                print(f"🗑️  Backup removed: {backup_file}")
        else:
            print("❌ Upgrade validation FAILED!")
            print("🔄 Triggering automatic rollback...")
            
            # Rollback deployment
            await self_tuning._rollback_deployment(upgrade_state)
            
            # Clean up upgrade state
            upgrade_state_file.unlink()
        
    except Exception as e:
        print(f"❌ Error checking pending upgrade: {e}")
        import traceback
        traceback.print_exc()
        
        # Don't crash on upgrade check errors
        print("⚠️  Continuing normal startup...")


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
    # Parse command-line arguments FIRST to check for debug flag
    parser = argparse.ArgumentParser(description="Sophia AI Assistant")
    # Default to event-driven autonomous operation as per AMI Phase 1.
    # Provide an explicit opt-out flag (--no-event-driven) for backwards
    # compatibility with scripts/tests that expect legacy blocking behavior.
    parser.add_argument(
        "--no-event-driven",
        action="store_true",
        help="Disable event-driven architecture and use legacy blocking loop",
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
        "--debug",
        action="store_true",
        help="Enable verbose debug logging (shows all plugin initialization, API calls, etc.)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force offline mode (use local LLM only, no cloud fallback)",
    )
    parser.add_argument(
        "--once", type=str, help="Single-run mode: process one input and exit (fast, no UI)"
    )
    parser.add_argument("input", nargs="*", help="Non-interactive input for single-run mode")
    args = parser.parse_args()

    # Configure logging level based on debug flag
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        print("🐛 DEBUG MODE ENABLED - Verbose logging active")
    else:
        # User-friendly mode: Only show warnings and errors in console
        logging.basicConfig(
            level=logging.WARNING,
            format='%(levelname)s: %(message)s'
        )
    
    # Suppress warnings AFTER logging is configured
    import warnings

    warnings.filterwarnings("ignore")
    os.environ["LANGFUSE_ENABLED"] = "false"

    check_venv()
    # .env already loaded at module level (before imports)

    # Determine UI style (CLI arg > ENV var > default CLASSIC for stability)
    ui_style = args.ui or os.getenv("SOPHIA_UI_STYLE", "classic")

    print("Starting Sophia's kernel...")
    # If the user explicitly disabled event-driven via CLI flag, honor it;
    # otherwise default to event-driven (AMI mode ON).
    if not args.no_event_driven:
        print("🚀 Event-driven architecture ENABLED (Phase 1)")
    if args.offline:
        print("🔒 OFFLINE MODE ENABLED - Local LLM only (no cloud fallback)")

    # Print UI style
    ui_icons = {
        "matrix": "🟢 MATRIX",
        "startrek": "🟡 STAR TREK LCARS",
        "cyberpunk": "🌈 CYBERPUNK",
        "classic": "⚪ CLASSIC",
    }
    print(f"🎨 UI Style: {ui_icons.get(ui_style, ui_style.upper())}")

    kernel = Kernel(use_event_driven=not args.no_event_driven, offline_mode=args.offline)

    # IMPORTANT: Initialize kernel to load all plugins
    await kernel.initialize()

    # PHASE 3.7: Check for pending autonomous upgrades
    await _check_pending_upgrade(kernel)

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
        print("🚫 Web UI disabled - terminal-only mode")
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
            offline_mode=args.offline,  # Pass offline mode flag
        )

        # Process single input with timeout
        # Note: Offline mode needs MUCH more time (planning with 8B model can take 3-5 minutes)
        try:
            response = await asyncio.wait_for(
                kernel.process_single_input(context),
                timeout=300.0,  # 5 minutes for offline planning + inference
            )
            print(f"\n✅ Sophia: {response}\n")
            sys.exit(0)
        except asyncio.TimeoutError:
            print("\n❌ Error: Response timeout (>300s)\n")
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
