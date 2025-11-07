#!/usr/bin/env bash
# Worker that watches ./autotasks directory for task files (.json) and runs them sequentially
# Usage: ./autonomous_worker.sh [poll-interval-seconds]

set -euo pipefail

AUTOTASK_DIR="autotasks"
RESULTS_DIR="autotask_results"
POLL_INTERVAL=${1:-5}
mkdir -p "$AUTOTASK_DIR" "$RESULTS_DIR"

echo "Autonomous worker started. Watching $AUTOTASK_DIR (poll every $POLL_INTERVAL s)"
while true; do
    # Find a JSON file
    task_file=$(ls -1t "$AUTOTASK_DIR"/*.json 2>/dev/null | head -1 || true)
    if [ -n "$task_file" ]; then
        echo "Found task file: $task_file"
        task_name=$(basename "$task_file" .json)
        # Move the file into a processing name to avoid double processing
        processing_file="${task_file}.processing"
        mv "$task_file" "$processing_file"
        echo "Processing $processing_file"
        # Run the session runner (Python version)
        python3 autonomous_session_runner.py "$task_name" "$processing_file" || echo "Task $task_name failed"
        # Move the .processing to results archive
        mv "$processing_file" "$RESULTS_DIR/${task_name}_processed_$(date +%Y%m%d_%H%M%S).json"
        echo "Task $task_name done"
    fi
    sleep $POLL_INTERVAL
done
