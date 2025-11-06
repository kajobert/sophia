#!/bin/bash
# Offline mode benchmark script for Jules API integration testing
# Usage: bash benchmark_offline.sh [--verbose] [--save]

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           SOPHIA OFFLINE MODE BENCHMARK - JULES API READY CHECK       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Ollama is running
echo -e "${YELLOW}[1/5]${NC} Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Ollama is not running!${NC}"
    echo -e "   Start with: ${YELLOW}ollama serve${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Ollama is running${NC}"

# Check model exists
echo -e "${YELLOW}[2/5]${NC} Checking llama3.1:8b model..."
if ! curl -s http://localhost:11434/api/show -d '{"name":"llama3.1:8b"}' | grep -q "llama3.1:8b"; then
    echo -e "${RED}❌ ERROR: llama3.1:8b model not found!${NC}"
    echo -e "   Pull with: ${YELLOW}ollama pull llama3.1:8b${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Model llama3.1:8b found${NC}"

# Check Python environment
echo -e "${YELLOW}[3/5]${NC} Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: python3 not found!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python ${PYTHON_VERSION}${NC}"

# Check dependencies
echo -e "${YELLOW}[4/5]${NC} Checking dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${RED}❌ ERROR: requests library not installed!${NC}"
    echo -e "   Install with: ${YELLOW}pip install requests${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dependencies OK${NC}"

# Run benchmark
echo -e "${YELLOW}[5/5]${NC} Running benchmark tests..."
echo ""

ARGS=""
if [[ "$*" == *"--verbose"* ]] || [[ "$*" == *"-v"* ]]; then
    ARGS="$ARGS --verbose"
fi
if [[ "$*" == *"--save"* ]] || [[ "$*" == *"-s"* ]]; then
    ARGS="$ARGS --save-results"
fi

python3 benchmark_offline_mode.py $ARGS
EXIT_CODE=$?

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}║  ✅ BENCHMARK PASSED - READY FOR JULES API INTEGRATION                ║${NC}"
elif [ $EXIT_CODE -eq 1 ]; then
    echo -e "${YELLOW}║  ⚠️  MOST TESTS PASSED - REVIEW FAILURES BEFORE JULES API             ║${NC}"
else
    echo -e "${RED}║  ❌ BENCHMARK FAILED - FIX ISSUES BEFORE JULES API                     ║${NC}"
fi

echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"

exit $EXIT_CODE
