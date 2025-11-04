#!/bin/bash
#
# Quick Setup Script for Local LLM with Sophia
# 
# This script will:
# 1. Check if Ollama is installed
# 2. Install Ollama if needed
# 3. Download recommended model (Gemma 2 2B)
# 4. Configure Sophia
# 5. Test the setup
#

set -e  # Exit on error

echo "🚀 Sophia Local LLM Setup"
echo "========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Ollama is installed
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is already installed"
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -1 || echo "unknown")
    print_info "Version: $OLLAMA_VERSION"
else
    print_info "Ollama not found. Installing..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Detected Linux. Installing via script..."
        curl -fsSL https://ollama.com/install.sh | sh
        print_success "Ollama installed"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Detected macOS. Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install ollama
            print_success "Ollama installed"
        else
            print_error "Homebrew not found. Please install from https://ollama.com/download"
            exit 1
        fi
    else
        print_error "Unsupported OS. Please install Ollama manually from https://ollama.com/download"
        exit 1
    fi
fi

echo ""
echo "Starting Ollama service..."
# Check if Ollama is already running
if pgrep -x "ollama" > /dev/null; then
    print_success "Ollama service is already running"
else
    # Start Ollama in background
    ollama serve &
    OLLAMA_PID=$!
    print_success "Ollama service started (PID: $OLLAMA_PID)"
    sleep 2  # Give it time to start
fi

echo ""
echo "Checking available models..."
MODELS=$(ollama list 2>&1 || echo "")

# Check if Gemma 2 2B is already downloaded
if echo "$MODELS" | grep -q "gemma2:2b"; then
    print_success "Gemma 2 2B is already downloaded"
else
    print_info "Downloading Gemma 2 2B (~1.6 GB)..."
    echo "This might take a few minutes depending on your internet speed..."
    ollama pull gemma2:2b
    print_success "Gemma 2 2B downloaded"
fi

echo ""
echo "Testing Ollama with a simple prompt..."
TEST_RESPONSE=$(ollama run gemma2:2b "Say 'Hello from Ollama!' and nothing else" 2>&1 || echo "ERROR")

if [[ "$TEST_RESPONSE" == *"Hello"* ]]; then
    print_success "Ollama is working correctly!"
    print_info "Response: $TEST_RESPONSE"
else
    print_error "Ollama test failed. Response: $TEST_RESPONSE"
    exit 1
fi

echo ""
echo "Configuring Sophia..."

# Check if config file exists
CONFIG_FILE="config/settings.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Config file not found: $CONFIG_FILE"
    print_info "Please run this script from the Sophia root directory"
    exit 1
fi

# Check if local_llm plugin is already configured
if grep -q "tool_local_llm:" "$CONFIG_FILE"; then
    print_success "Local LLM plugin already configured in settings.yaml"
else
    print_info "Adding local LLM configuration to settings.yaml..."
    
    # Add configuration (basic YAML append)
    cat >> "$CONFIG_FILE" << 'EOF'

  # Local LLM Plugin (Ollama)
  tool_local_llm:
    enabled: true
    local_llm:
      runtime: "ollama"
      base_url: "http://localhost:11434"
      model: "gemma2:2b"
      timeout: 120
      max_tokens: 2048
      temperature: 0.7
EOF
    
    print_success "Configuration added"
fi

echo ""
echo "═══════════════════════════════════════════"
print_success "Setup Complete! 🎉"
echo "═══════════════════════════════════════════"
echo ""
echo "Available models:"
ollama list
echo ""
echo "Next steps:"
echo "  1. Start Sophia: python run.py"
echo "  2. Test local LLM: 'Check local LLM status'"
echo "  3. Use it: 'Use local LLM to explain Python async'"
echo ""
echo "📚 Full documentation: docs/en/LOCAL_LLM_SETUP.md"
echo ""
echo "💡 Recommended models for your Lenovo Legend:"
echo "  - gemma2:2b    (fastest, 1.6GB) ← Already installed!"
echo "  - llama3.2:3b  (balanced, 2GB)"
echo "  - phi3:mini    (coding, 2.3GB)"
echo "  - llama3.1:8b  (quality, 4.7GB)"
echo ""
echo "To download more models:"
echo "  ollama pull llama3.2:3b"
echo "  ollama pull phi3:mini"
echo ""
print_success "Ready to use local LLM! 🚀"
