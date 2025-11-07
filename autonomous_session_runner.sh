#!/usr/bin/env bash
# Run a multi-step autonomous session against SOPHIA
# Usage: ./autonomous_session_runner.sh <task-name> <instructions-file.json>
# instructions-file.json: JSON array of objects { "id": "step1", "instruction": "..." }

set -euo pipefail

TASK_NAME=${1:-autotask}
INSTRUCTIONS_FILE=${2:-}
BASE_DIR="autotasks"
RESULTS_DIR="autotask_results"
LOG_DIR="test_results"
mkdir -p "$BASE_DIR" "$RESULTS_DIR" "$LOG_DIR"

if [ -z "$INSTRUCTIONS_FILE" ]; then
    echo "Usage: $0 <task-name> <instructions-file.json>"
    exit 2
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_DIR="$RESULTS_DIR/${TASK_NAME}_${TIMESTAMP}"
mkdir -p "$SESSION_DIR"
cp "$INSTRUCTIONS_FILE" "$SESSION_DIR/instructions.json"

# Read JSON array of instructions
INSTRUCTIONS=$(cat "$INSTRUCTIONS_FILE")

# For each instruction, send to /api/enqueue and wait for completion
# Long timeout for each step (default 30 minutes)
STEP_TIMEOUT=${STEP_TIMEOUT:-1800}  # seconds
POLL_INTERVAL=${POLL_INTERVAL:-5}

# Helper: post instruction and return task_id
post_instruction() {
    local instr="$1"
    local resp
    resp=$(curl -s -X POST http://127.0.0.1:8000/api/enqueue -H "Content-Type: application/json" -d "{\"instruction\": \"${instr//"/\\\"}\"}")
    echo "$resp"
}

# Helper: wait for completion by checking logs for either task_id or "Response ready"
wait_for_completion() {
    local task_id="$1"
    local max_wait=$2
    local waited=0
    echo "Waiting up to ${max_wait}s for task ${task_id} to complete..."
    while [ $waited -lt $max_wait ]; do
        # Look for lines mentioning task_id or common completion markers
        if tail -200 logs/sophia.log | grep -q "task_id\|Response ready\|Execution completed\|Step .* completed"; then
            # Narrow check: if task_id appears, consider complete; else check for Response ready
            if [ -n "$task_id" ] && tail -500 logs/sophia.log | grep -q "${task_id}"; then
                echo "Detected task_id ${task_id} in logs"
                return 0
            fi
            if tail -200 logs/sophia.log | grep -q "Response ready\|Execution completed"; then
                echo "Detected completion marker in logs"
                return 0
            fi
        fi
        sleep $POLL_INTERVAL
        waited=$((waited+POLL_INTERVAL))
    done
    return 1
}

# Parse instructions using python (more portable than jq)
len=$(python3 -c "import json,sys; print(len(json.load(sys.stdin)))" < "$INSTRUCTIONS_FILE" 2>/dev/null || echo "0")
if [ "$len" -eq 0 ]; then
    echo "No instructions found in $INSTRUCTIONS_FILE"
    exit 1
fi

echo "Starting autonomous session: $TASK_NAME -> $len steps"

# Process each instruction
step_index=0
python3 << 'PYEOF' "$INSTRUCTIONS_FILE" | while IFS= read -r step_data; do
import json, sys
with open(sys.argv[1]) as f:
    for item in json.load(f):
        print(json.dumps(item))
PYEOF

step_index=$((step_index+1))
step_id=$(echo "$step_data" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("id", "step_'$step_index'"))')
instruction_text=$(echo "$step_data" | python3 -c 'import json,sys; print(json.load(sys.stdin)["instruction"])')
    echo "--- Step $step_index/$len: $step_id" | tee "$SESSION_DIR/step_${step_index}_meta.txt"
    echo "Instruction: $instruction_text" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"

    # Post instruction
    post_resp=$(post_instruction "$instruction_text")
    echo "Post response: $post_resp" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"

    task_id=$(echo "$post_resp" | python3 -c "import json,sys; obj=json.load(sys.stdin); print(obj.get('task_id', ''))" 2>/dev/null || echo "")
    echo "Task ID: $task_id" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"

    # Wait for completion
    if [ -n "$task_id" ]; then
        if wait_for_completion "$task_id" $STEP_TIMEOUT; then
            echo "Step $step_index completed (task_id $task_id)" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"
        else
            echo "WARN: Step $step_index did not complete within timeout ($STEP_TIMEOUT s)" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"
        fi
    else
        # If no task_id, fallback to waiting for Response ready
        if wait_for_completion "" $STEP_TIMEOUT; then
            echo "Step $step_index completed (no task_id reported)" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"
        else
            echo "WARN: Step $step_index did not complete within timeout (no task_id issued)" | tee -a "$SESSION_DIR/step_${step_index}_meta.txt"
        fi
    fi

    # Capture recent logs and planner output
    tail -200 logs/sophia.log > "$SESSION_DIR/step_${step_index}_logs_tail.txt"
    grep -A 8 "Raw LLM response received in planner" "$SESSION_DIR/step_${step_index}_logs_tail.txt" > "$SESSION_DIR/step_${step_index}_planner.txt" || true
    # Capture response ready lines
    grep "Response ready" "$SESSION_DIR/step_${step_index}_logs_tail.txt" > "$SESSION_DIR/step_${step_index}_response_ready.txt" || true

    # Sleep a small cooldown to allow system stabilize
    sleep 2
done

# Summarize session
echo "Autonomous session complete. Results saved in $SESSION_DIR"
ls -la "$SESSION_DIR"

# Exit with success
exit 0
