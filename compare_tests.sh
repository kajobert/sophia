#!/bin/bash
# Compare test results
# Usage: ./compare_tests.sh

TEST_DIR="test_results"

if [ ! -d "$TEST_DIR" ]; then
    echo "❌ No test results found"
    exit 1
fi

echo "=================================================="
echo "TEST RESULTS COMPARISON"
echo "=================================================="
echo ""
echo "Available tests:"
ls -t "$TEST_DIR"/test_*.txt | nl
echo ""

# Show summary of all tests
echo "=================================================="
echo "SUMMARY"
echo "=================================================="
printf "%-5s %-20s %-10s %-10s %-20s\n" "No." "Timestamp" "Steps" "Errors" "Status"
echo "------------------------------------------------------------------"

ls -t "$TEST_DIR"/test_*.txt | nl | while read num file; do
    if [ -f "$file" ]; then
        timestamp=$(basename "$file" | sed 's/test_\(.*\)\.txt/\1/')
        steps=$(grep "Steps executed:" "$file" | awk '{print $3}')
        errors=$(grep "^Errors:" "$file" | awk '{print $2}')
        status=$(grep "^Status:" "$file" | awk '{$1=""; print $0}' | xargs)
        
        printf "%-5s %-20s %-10s %-10s %-20s\n" "$num" "$timestamp" "$steps" "$errors" "$status"
    fi
done

echo ""
echo "=================================================="
echo "To view specific test: ./show_test_results.sh <number>"
echo "=================================================="
