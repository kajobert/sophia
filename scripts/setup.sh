#!/bin/bash
# ==============================================================================
# Nomad AI Agent Orchestrator - Installation & Setup Script
#
# Performs complete local development environment setup.
# For production deployment, see: docs/DEPLOYMENT.md
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Nomad Setup - Local Development Environment"
echo "=============================================="
echo "Project: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# --- Step 1: Prerequisites Check ---
echo "🔍 Checking prerequisites..."

# Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION"

# Git
if ! command -v git &> /dev/null; then
    echo "⚠️  Git not found (optional for development)"
fi

# --- Step 2: Virtual Environment ---
echo ""
echo "📦 Setting up virtual environment..."

if [ ! -d "venv" ]; then
    echo "Creating virtual environment in ./venv..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate

# --- Step 3: Dependency Installation ---
echo ""
echo "📥 Installing dependencies..."

# Upgrade pip
pip install --upgrade pip

# Install from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo "✅ Dependencies installed"

# --- Step 4: Environment Configuration ---
echo ""
echo "⚙️  Configuring environment..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
        echo "   - GEMINI_API_KEY (required)"
        echo "   - OPENROUTER_API_KEY (optional)"
        echo ""
    else
        echo "⚠️  .env.example not found, creating minimal .env..."
        cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=
NOMAD_PORT=8080
NOMAD_ENV=development
EOF
        echo "✅ Created minimal .env"
    fi
else
    echo "✅ .env already exists"
fi

# --- Step 5: Directory Structure ---
echo ""
echo "📁 Creating directory structure..."

mkdir -p logs memory sandbox
echo "✅ Directories created"

# --- Step 6: Verification Tests ---
echo ""
echo "🧪 Running verification tests..."

# Run tests with pytest
if python -m pytest tests/ -v --tb=short -x 2>&1 | tee /tmp/nomad_test_output.txt; then
    TEST_COUNT=$(grep -c "PASSED" /tmp/nomad_test_output.txt || echo "0")
    echo ""
    echo "✅ Tests completed: $TEST_COUNT passed"
else
    echo ""
    echo "⚠️  Some tests failed (this is OK for initial setup)"
fi

# --- Step 7: Final Instructions ---
echo ""
echo "=============================================="
echo "✅ Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure API keys in .env file"
echo "2. Start backend:  ./scripts/start_backend.sh"
echo "3. Start TUI:      ./scripts/start_tui.sh"
echo "4. Or both:        ./scripts/start_nomad.sh"
echo ""
echo "For production deployment:"
echo "  - Docker:        docker-compose up -d"
echo "  - Systemd:       see docs/DEPLOYMENT.md"
echo ""
echo "Documentation:"
echo "  - README.md              - Project overview"
echo "  - docs/QUICKSTART.md     - Getting started"
echo "  - docs/DEPLOYMENT.md     - Production setup"
echo "  - docs/DEVELOPER_GUIDE.md - Development guide"
echo ""
