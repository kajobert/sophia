#!/bin/bash

# run_recovery_mission.sh
#
# Starts a Nomad mission with the content of a log file as the initial context.
# This is used to allow the agent to attempt to recover from a previous crash or error.
#
# Usage:
#   ./scripts/run_recovery_mission.sh <path_to_log_file> "<mission_goal>"

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path_to_log_file> \"<mission_goal>\""
    exit 1
fi

LOG_FILE="$1"
MISSION_GOAL="$2"

if [ ! -f "$LOG_FILE" ]; then
    echo "Error: Log file not found at '$LOG_FILE'"
    exit 1
fi

# Read the log file content
INITIAL_CONTEXT=$(cat "$LOG_FILE")

# Set the project root directory
PROJECT_ROOT=$(dirname "$0")/..
cd "$PROJECT_ROOT"

# Activate virtual environment
source .venv/bin/activate

# Construct the Python command to execute the mission
# We pass the mission goal and the initial context as arguments
# to a small Python script that will call the orchestrator.

RECOVERY_RUNNER_SCRIPT=$(mktemp)
cat > "$RECOVERY_RUNNER_SCRIPT" << EOL
import asyncio
import sys
from core.nomad_orchestrator_v2 import NomadOrchestratorV2

async def main():
    mission_goal = sys.argv[1]
    initial_context = sys.argv[2]

    orchestrator = NomadOrchestratorV2()
    await orchestrator.initialize()
    await orchestrator.execute_mission(mission_goal, initial_context=initial_context)
    await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
EOL

echo "Starting recovery mission..."
PYTHONPATH=. python "$RECOVERY_RUNNER_SCRIPT" "$MISSION_GOAL" "$INITIAL_CONTEXT"

# Clean up the temporary script
rm "$RECOVERY_RUNNER_SCRIPT"

echo "Recovery mission finished."