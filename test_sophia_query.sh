#!/bin/bash
# Test script for sending queries to SOPHIA and capturing full context
# Usage: ./test_sophia_query.sh "Your query here"

set -e  # Exit on error

QUERY="${1:-Přečti soubor roberts-notes.txt}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_DIR="test_results"
RESULT_FILE="${TEST_DIR}/test_${TIMESTAMP}.txt"
LOG_SNAPSHOT="${TEST_DIR}/logs_${TIMESTAMP}.txt"

# Create test results directory
mkdir -p "$TEST_DIR"

echo "========================================" | tee "$RESULT_FILE"
echo "SOPHIA Query Test - $TIMESTAMP" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "" | tee -a "$RESULT_FILE"
echo "Query: $QUERY" | tee -a "$RESULT_FILE"
echo "" | tee -a "$RESULT_FILE"

# Check if SOPHIA is running
if ! pgrep -f "run.py" > /dev/null; then
    echo "❌ SOPHIA is not running!" | tee -a "$RESULT_FILE"
    echo "Start it with: sophia-start" | tee -a "$RESULT_FILE"
    exit 1
fi

SOPHIA_PID=$(pgrep -f "run.py")
echo "✅ SOPHIA is running (PID: $SOPHIA_PID)" | tee -a "$RESULT_FILE"
echo "" | tee -a "$RESULT_FILE"

# Capture log state BEFORE query
echo "📋 Capturing pre-query log snapshot..." | tee -a "$RESULT_FILE"
tail -50 logs/sophia.log > "${TEST_DIR}/logs_before_${TIMESTAMP}.txt"

# Send query via HTTP API
echo "📤 Sending query to SOPHIA..." | tee -a "$RESULT_FILE"
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/enqueue \
    -H "Content-Type: application/json" \
    -d "{\"instruction\": \"$QUERY\"}" 2>&1)

CURL_EXIT=$?

if [ $CURL_EXIT -ne 0 ]; then
    echo "❌ Failed to send query (curl exit code: $CURL_EXIT)" | tee -a "$RESULT_FILE"
    echo "Response: $RESPONSE" | tee -a "$RESULT_FILE"
    exit 1
fi

echo "✅ Query sent successfully" | tee -a "$RESULT_FILE"
echo "" | tee -a "$RESULT_FILE"

# Wait for processing (check for completion signals in logs)
echo "⏳ Waiting for SOPHIA to process (max 120s)..." | tee -a "$RESULT_FILE"

# Extract task ID from response
TASK_ID=$(echo "$RESPONSE" | grep -o '"task_id":[0-9]*' | grep -o '[0-9]*')

if [ -z "$TASK_ID" ]; then
    echo "⚠️  Could not extract task_id from response" | tee -a "$RESULT_FILE"
else
    echo "📝 Task ID: $TASK_ID" | tee -a "$RESULT_FILE"
fi

TIMEOUT=120
ELAPSED=0
COMPLETED=false

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if kernel started processing (any activity in last 5 seconds)
    RECENT_ACTIVITY=$(tail -20 logs/sophia.log | grep "$(date -d '5 seconds ago' +'%Y-%m-%d %H:%M' 2>/dev/null || date +'%Y-%m-%d %H:%M')" | wc -l)
    
    # Check if response is ready (look for common completion patterns)
    if tail -100 logs/sophia.log | grep -q "Response ready\|Execution completed\|Phase 3: RESPONDING"; then
        COMPLETED=true
        break
    fi
    
    # Check for critical errors
    if tail -20 logs/sophia.log | grep -q "Planner failed\|No plan generated\|All execution steps failed"; then
        echo "⚠️  Critical error detected in logs" | tee -a "$RESULT_FILE"
        break
    fi
    
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    
    # Show progress every 10 seconds
    if [ $((ELAPSED % 10)) -eq 0 ]; then
        echo "  ... still processing ($ELAPSED s)" | tee -a "$RESULT_FILE"
    fi
done

if [ "$COMPLETED" = true ]; then
    echo "✅ Processing completed in ${ELAPSED}s" | tee -a "$RESULT_FILE"
else
    echo "⚠️  Timeout or no completion signal after ${ELAPSED}s" | tee -a "$RESULT_FILE"
fi

echo "" | tee -a "$RESULT_FILE"

# Capture logs AFTER query
echo "📋 Capturing post-query logs..." | tee -a "$RESULT_FILE"
tail -100 logs/sophia.log > "$LOG_SNAPSHOT"

# Extract relevant log sections
echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "PLANNER OUTPUT" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
grep -A 5 "Raw LLM response received in planner" "$LOG_SNAPSHOT" | tail -20 | tee -a "$RESULT_FILE" || echo "No planner output found" | tee -a "$RESULT_FILE"

echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "EXECUTION STEPS" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
grep "Step [0-9]/[0-9]:\|completed\|Step.*executed" "$LOG_SNAPSHOT" | tail -20 | tee -a "$RESULT_FILE" || echo "No execution steps found" | tee -a "$RESULT_FILE"

echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "ERRORS & WARNINGS" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
grep -E "ERROR|WARNING" "$LOG_SNAPSHOT" | tail -20 | tee -a "$RESULT_FILE" || echo "No errors or warnings" | tee -a "$RESULT_FILE"

echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "RESPONSE" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
grep "Response ready:" "$LOG_SNAPSHOT" | tail -3 | tee -a "$RESULT_FILE" || echo "No response found in logs" | tee -a "$RESULT_FILE"

echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "API RESPONSE" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "$RESPONSE" | tee -a "$RESULT_FILE"

echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "TEST SUMMARY" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"

# Count steps executed (grep -c může vrátit více řádků, bere první)
STEPS_EXECUTED=$(grep "Step [0-9]/[0-9]:" "$LOG_SNAPSHOT" 2>/dev/null | wc -l)
echo "Steps executed: $STEPS_EXECUTED" | tee -a "$RESULT_FILE"

# Count errors (exclude known non-critical errors)
ERROR_COUNT=$(grep "ERROR" "$LOG_SNAPSHOT" 2>/dev/null | grep -v "no such column\|NoneType can't be used in 'await'" | wc -l)
echo "Errors: $ERROR_COUNT" | tee -a "$RESULT_FILE"

# Check if plan was generated
if grep -q "No plan generated\|Planner failed" "$LOG_SNAPSHOT"; then
    echo "Status: ❌ FAILED - No plan generated" | tee -a "$RESULT_FILE"
elif grep -q "ERROR" "$LOG_SNAPSHOT" | grep -v "no such column\|NoneType can't be used in 'await'"; then
    echo "Status: ⚠️  COMPLETED WITH ERRORS" | tee -a "$RESULT_FILE"
elif [ "$STEPS_EXECUTED" -gt 0 ]; then
    echo "Status: ✅ SUCCESS" | tee -a "$RESULT_FILE"
else
    echo "Status: ⚠️  UNCERTAIN" | tee -a "$RESULT_FILE"
fi

echo "" | tee -a "$RESULT_FILE"
echo "Full logs saved to: $LOG_SNAPSHOT" | tee -a "$RESULT_FILE"
echo "Test results saved to: $RESULT_FILE" | tee -a "$RESULT_FILE"
echo "" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
echo "To view full results: cat $RESULT_FILE" | tee -a "$RESULT_FILE"
echo "To view logs: cat $LOG_SNAPSHOT" | tee -a "$RESULT_FILE"
echo "========================================" | tee -a "$RESULT_FILE"
