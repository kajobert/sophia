import os
import sys
import argparse
import asyncio

# Add project root to Python path to allow sibling module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.nomad_orchestrator_v2 import NomadOrchestratorV2
from core.rich_printer import RichPrinter

async def main():
    """
    Main function to run a local mission for the Nomad agent.
    """
    # 1. Check for API Key
    if "OPENROUTER_API_KEY" not in os.environ:
        RichPrinter.error("FATAL: The OPENROUTER_API_KEY environment variable is not set.")
        sys.exit(1)

    # 2. Setup Argument Parser
    parser = argparse.ArgumentParser(
        description="Run a local mission with the Nomad Orchestrator.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "mission_goal",
        type=str,
        help="The main objective for the agent to accomplish."
    )
    args = parser.parse_args()

    orchestrator = NomadOrchestratorV2(project_root=".")

    try:
        # Initialize all components, including MCP servers
        await orchestrator.initialize()

        # Execute the mission with the provided goal
        await orchestrator.execute_mission(args.mission_goal)

    except Exception as e:
        RichPrinter.error(f"An unexpected error occurred during the mission: {e}")
    finally:
        # Ensure all background processes are terminated
        RichPrinter.info("Mission finished. Cleaning up resources...")
        await orchestrator.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        RichPrinter.warning("\nMission interrupted by user. Shutting down...")
    except Exception as e:
        RichPrinter.error(f"A top-level error occurred: {e}")