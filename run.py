import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

from core.kernel import Kernel


def check_venv():
    """Check if the application is running in a virtual environment."""
    if sys.prefix == sys.base_prefix:
        print("---")
        print("ERROR: Application not in a virtual environment.")
        print("Please activate it, e.g., 'source .venv/bin/activate'")
        print("---")
        sys.exit(1)


async def main():
    """Initializes and runs the Sophia Kernel in autonomous mode."""
    # --- Environment & Logging Setup ---
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    if log_level == "DEBUG":
        print("🐛 DEBUG MODE ENABLED - Verbose logging active")

    # Suppress third-party library warnings
    import warnings
    warnings.filterwarnings("ignore")
    os.environ["LANGFUSE_ENABLED"] = "false"

    check_venv()

    # --- Kernel Initialization ---
    print("Starting Sophia's kernel in autonomous mode...")

    offline_mode = os.getenv("SOPHIA_OFFLINE_MODE", "false").lower() == "true"
    if offline_mode:
        print("🔒 OFFLINE MODE ENABLED - Local LLM only")

    # Kernel is now always event-driven
    kernel = Kernel(use_event_driven=True, offline_mode=offline_mode)
    await kernel.initialize()

    # --- Autonomous Operation ---
    # This is the main, non-terminating loop.
    await kernel.run_autonomous_mode()

    print("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sophia shutting down...")
