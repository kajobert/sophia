#!/bin/bash
# Sophia WSL2 Auto-Install Script
# Automated installation for Windows WSL2 + Ubuntu environment
# Version: 1.0.0
# Date: 2025-11-04

set -e  # Exit on error

echo "🚀 Sophia WSL2 Auto-Install Script"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    echo -e "${RED}❌ Error: This script must be run in WSL2!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running in WSL2${NC}"
echo ""

# Step 1: Update system
echo "📦 Step 1/8: Updating Ubuntu packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python 3.12 and dev tools
echo "🐍 Step 2/8: Installing Python 3.12..."
if ! command -v python3.12 &> /dev/null; then
    # Check Ubuntu version
    UBUNTU_VERSION=$(lsb_release -rs)
    if [[ "$UBUNTU_VERSION" == "24.04" ]]; then
        echo "Ubuntu 24.04 detected - Python 3.12 included"
        sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
    else
        echo "Adding deadsnakes PPA for Python 3.12..."
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
    fi
else
    echo -e "${GREEN}✅ Python 3.12 already installed${NC}"
fi

# Step 3: Install uv (fast Python package manager)
echo "⚡ Step 3/8: Installing uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo -e "${GREEN}✅ uv already installed${NC}"
fi

# Step 4: Install Git
echo "📝 Step 4/8: Installing Git..."
if ! command -v git &> /dev/null; then
    sudo apt install -y git
else
    echo -e "${GREEN}✅ Git already installed${NC}"
fi

# Step 5: Clone Sophia repository (if not already cloned)
echo "📥 Step 5/8: Checking Sophia repository..."
SOPHIA_DIR="$HOME/sophia"
if [ ! -d "$SOPHIA_DIR" ]; then
    echo "Cloning Sophia repository..."
    git clone https://github.com/ShotyCZ/sophia.git "$SOPHIA_DIR"
    cd "$SOPHIA_DIR"
    git checkout feature/year-2030-ami-complete
else
    echo -e "${GREEN}✅ Sophia repository exists${NC}"
    cd "$SOPHIA_DIR"
    echo "Pulling latest changes..."
    git fetch origin
    git checkout feature/year-2030-ami-complete
    git pull origin feature/year-2030-ami-complete
fi

# Step 6: Create virtual environment
echo "🏗️  Step 6/8: Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3.12 -m venv .venv
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Step 7: Install dependencies
echo "📚 Step 7/8: Installing dependencies with uv..."
source .venv/bin/activate
/home/$USER/.local/bin/uv pip sync requirements-dev.txt

# Step 8: Install Ollama (optional)
echo "🤖 Step 8/8: Installing Ollama (local LLM)..."
read -p "Do you want to install Ollama for local LLM? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ! command -v ollama &> /dev/null; then
        curl -fsSL https://ollama.com/install.sh | sh
        echo "Starting Ollama server..."
        ollama serve > /dev/null 2>&1 &
        sleep 3
        echo "Downloading Llama 3.1 8B model (4.7GB - this will take a while)..."
        ollama pull llama3.1:8b
    else
        echo -e "${GREEN}✅ Ollama already installed${NC}"
    fi
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Sophia V2 - Offline Configuration
# Full offline mode with local LLM only

# ============================================================================
# LOCAL LLM CONFIGURATION (Ollama + Llama 3.1 8B)
# ============================================================================
LOCAL_LLM_RUNTIME=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3.1:8b
LOCAL_LLM_TIMEOUT=120
LOCAL_LLM_MAX_TOKENS=4096
LOCAL_LLM_TEMPERATURE=0.7

# ============================================================================
# OPTIONAL: API Keys (leave empty for offline mode)
# ============================================================================
# TAVILY_API_KEY=
# JULES_API_KEY=
# GITHUB_TOKEN=
EOF
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "🎉 Sophia is ready to use!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   cd $SOPHIA_DIR"
echo "   source .venv/bin/activate"
echo ""
echo "2. Run tests:"
echo "   pytest tests/ -m 'not integration' -v"
echo ""
echo "3. Start Sophia:"
echo "   python run.py"
echo ""
echo "4. (Optional) Add API keys to .env:"
echo "   nano .env"
echo ""
echo "📚 Documentation: docs/WINDOWS_WSL2_SETUP.md"
echo "🆘 Troubleshooting: docs/WINDOWS_QUICK_REFERENCE.md"
