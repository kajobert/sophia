#!/bin/bash
# Model Comparison Test Script
# Tests: GPT-4o-mini (online) vs llama3.1:8b vs qwen2.5:14b

TEST_QUERY="Ahoj Sophie, jaké máš k dispozici nástroje?"
LOG_DIR="test_results"
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "🧪 SOPHIA Model Comparison Test"
echo "=========================================="
echo "Query: $TEST_QUERY"
echo ""

# Function to extract plan from logs
extract_plan() {
    local log_file=$1
    local model_name=$2
    
    echo "=== $model_name PLAN ===" >> "$LOG_DIR/comparison_report.txt"
    
    # Get last Raw LLM response
    grep "Raw LLM response" "$log_file" | tail -1 | python3 -c "
import sys, json
try:
    line = sys.stdin.read()
    data = json.loads(line)
    msg = data.get('message', '')
    if 'Raw LLM response' in msg:
        plan_str = msg.split('): ')[1]
        plan = json.loads(plan_str)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
except Exception as e:
    print(f'Error: {e}')
" >> "$LOG_DIR/comparison_report.txt"
    
    echo "" >> "$LOG_DIR/comparison_report.txt"
}

# Function to extract response
extract_response() {
    local log_file=$1
    local model_name=$2
    
    echo "=== $model_name RESPONSE ===" >> "$LOG_DIR/comparison_report.txt"
    
    grep "Response ready:" "$log_file" | tail -1 | python3 -c "
import sys, json
try:
    line = sys.stdin.read()
    data = json.loads(line)
    msg = data['message']
    response = msg.replace('🎯 [Kernel] Response ready: ', '')
    print(response[:500])
except Exception as e:
    print(f'Error: {e}')
" >> "$LOG_DIR/comparison_report.txt"
    
    echo "" >> "$LOG_DIR/comparison_report.txt"
    echo "---" >> "$LOG_DIR/comparison_report.txt"
    echo "" >> "$LOG_DIR/comparison_report.txt"
}

# Initialize report
echo "# Model Comparison Report - $(date)" > "$LOG_DIR/comparison_report.txt"
echo "Query: \"$TEST_QUERY\"" >> "$LOG_DIR/comparison_report.txt"
echo "" >> "$LOG_DIR/comparison_report.txt"

# Current test (GPT-4o-mini should be running)
echo "📊 Testing current configuration (should be GPT-4o-mini)..."
echo "Check logs and Dashboard Chat manually"
echo ""
echo "After testing in Dashboard, check:"
echo "  tail -100 logs/sophia.log | grep -E 'Raw LLM response|Response ready'"
echo ""
echo "Report will be in: $LOG_DIR/comparison_report.txt"
