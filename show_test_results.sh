#!/bin/bash
# Show latest test results
# Usage: ./show_test_results.sh [test_number]

TEST_DIR="test_results"

if [ ! -d "$TEST_DIR" ]; then
    echo "❌ No test results found (directory $TEST_DIR doesn't exist)"
    exit 1
fi

if [ -n "$1" ]; then
    # Show specific test by timestamp or number
    RESULT_FILE=$(ls -t "$TEST_DIR"/test_*.txt 2>/dev/null | sed -n "${1}p")
    if [ -z "$RESULT_FILE" ]; then
        echo "❌ Test #$1 not found"
        echo "Available tests:"
        ls -t "$TEST_DIR"/test_*.txt 2>/dev/null | nl
        exit 1
    fi
else
    # Show latest test
    RESULT_FILE=$(ls -t "$TEST_DIR"/test_*.txt 2>/dev/null | head -1)
fi

if [ -z "$RESULT_FILE" ]; then
    echo "❌ No test results found"
    exit 1
fi

echo "=================================================="
echo "Showing: $(basename "$RESULT_FILE")"
echo "=================================================="
echo ""
cat "$RESULT_FILE"
echo ""
echo "=================================================="
echo "Available tests:"
ls -t "$TEST_DIR"/test_*.txt 2>/dev/null | nl
echo "=================================================="
