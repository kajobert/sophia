#!/bin/bash
# ==============================================================================
# Nomad AI Agent - Production Installation Script
#
# Installs Nomad as a system service with systemd integration.
# Run with sudo: sudo ./scripts/install-production.sh
#
# Prerequisites:
#   - Python 3.12+
#   - systemd
#   - root/sudo access
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_USER="nomad"
INSTALL_GROUP="nomad"
INSTALL_DIR="/opt/nomad"
SERVICE_FILES=("nomad-backend.service" "nomad-tui@.service")
PYTHON_MIN_VERSION="3.12"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Nomad Production Installation${NC}"
echo "=================================="
echo ""

# --- Step 1: Prerequisites Check ---
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Python version check
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]; }; then
    echo -e "${RED}❌ Python $PYTHON_MIN_VERSION or higher required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# Systemd check
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}❌ systemd not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ systemd available${NC}"

# Git check (optional)
if command -v git &> /dev/null; then
    echo -e "${GREEN}✅ git available${NC}"
else
    echo -e "${YELLOW}⚠️  git not found (optional)${NC}"
fi

# --- Step 2: User and Group Creation ---
echo ""
echo -e "${YELLOW}👤 Setting up system user...${NC}"

if id "$INSTALL_USER" &>/dev/null; then
    echo -e "${GREEN}✅ User '$INSTALL_USER' already exists${NC}"
else
    useradd --system --home-dir "$INSTALL_DIR" --shell /bin/bash --comment "Nomad AI Agent" "$INSTALL_USER"
    echo -e "${GREEN}✅ Created system user '$INSTALL_USER'${NC}"
fi

# --- Step 3: Directory Setup ---
echo ""
echo -e "${YELLOW}📁 Creating directory structure...${NC}"

mkdir -p "$INSTALL_DIR"/{logs,memory,sandbox,backups}
mkdir -p "$INSTALL_DIR/venv"

echo -e "${GREEN}✅ Directories created in $INSTALL_DIR${NC}"

# --- Step 4: Copy Application Files ---
echo ""
echo -e "${YELLOW}📦 Copying application files...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Copy application code
rsync -av --exclude='venv' --exclude='.venv' --exclude='__pycache__' \
          --exclude='*.pyc' --exclude='.git' --exclude='logs' \
          --exclude='memory' --exclude='sandbox' \
          "$PROJECT_ROOT/" "$INSTALL_DIR/"

echo -e "${GREEN}✅ Application files copied${NC}"

# --- Step 5: Virtual Environment ---
echo ""
echo -e "${YELLOW}🐍 Creating virtual environment...${NC}"

cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Virtual environment created and dependencies installed${NC}"

# --- Step 6: Configuration ---
echo ""
echo -e "${YELLOW}⚙️  Setting up configuration...${NC}"

if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f "$INSTALL_DIR/.env.production.example" ]; then
        cp "$INSTALL_DIR/.env.production.example" "$INSTALL_DIR/.env"
        echo -e "${GREEN}✅ Created .env from .env.production.example${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit $INSTALL_DIR/.env and add API keys!${NC}"
    else
        echo -e "${RED}❌ .env.production.example not found!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi

# Set ownership
chown -R "$INSTALL_USER:$INSTALL_GROUP" "$INSTALL_DIR"
chmod 600 "$INSTALL_DIR/.env"

echo -e "${GREEN}✅ Configuration files set up${NC}"

# --- Step 7: Systemd Service Installation ---
echo ""
echo -e "${YELLOW}⚙️  Installing systemd services...${NC}"

for service_file in "${SERVICE_FILES[@]}"; do
    if [ -f "$INSTALL_DIR/systemd/$service_file" ]; then
        cp "$INSTALL_DIR/systemd/$service_file" "/etc/systemd/system/"
        echo -e "${GREEN}✅ Installed $service_file${NC}"
    else
        echo -e "${YELLOW}⚠️  $service_file not found, skipping${NC}"
    fi
done

# Reload systemd
systemctl daemon-reload

echo -e "${GREEN}✅ Systemd services installed${NC}"

# --- Step 8: Enable and Start Backend Service ---
echo ""
echo -e "${YELLOW}🚀 Starting Nomad backend service...${NC}"

systemctl enable nomad-backend.service
systemctl start nomad-backend.service

# Wait a moment for startup
sleep 3

# Check status
if systemctl is-active --quiet nomad-backend.service; then
    echo -e "${GREEN}✅ Backend service is running${NC}"
else
    echo -e "${RED}❌ Backend service failed to start${NC}"
    echo "Check logs with: journalctl -u nomad-backend.service -n 50"
    exit 1
fi

# --- Step 9: Health Check ---
echo ""
echo -e "${YELLOW}🏥 Running health check...${NC}"

sleep 2

if curl -f http://localhost:8080/api/v1/health/ping &> /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed (service may still be starting)${NC}"
fi

# --- Step 10: Final Instructions ---
echo ""
echo "=============================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "Service Management:"
echo "  Status:   systemctl status nomad-backend"
echo "  Stop:     systemctl stop nomad-backend"
echo "  Start:    systemctl start nomad-backend"
echo "  Restart:  systemctl restart nomad-backend"
echo "  Logs:     journalctl -u nomad-backend -f"
echo ""
echo "TUI Client (per-user):"
echo "  Start:    systemctl --user start nomad-tui@\$USER"
echo "  Stop:     systemctl --user stop nomad-tui@\$USER"
echo ""
echo "Configuration:"
echo "  API Keys: $INSTALL_DIR/.env"
echo "  Config:   $INSTALL_DIR/config/production.yaml"
echo "  Logs:     $INSTALL_DIR/logs/"
echo ""
echo "Next Steps:"
echo "  1. Edit $INSTALL_DIR/.env and add API keys"
echo "  2. Restart backend: systemctl restart nomad-backend"
echo "  3. Check status: systemctl status nomad-backend"
echo "  4. View API: http://localhost:8080/docs"
echo ""
echo "For uninstallation, run: sudo ./scripts/uninstall-production.sh"
echo ""
