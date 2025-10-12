#!/bin/bash
# ==============================================================================
# Nomad AI Agent - Production Uninstallation Script
#
# Removes Nomad system service and all related files.
# Run with sudo: sudo ./scripts/uninstall-production.sh
#
# WARNING: This will delete all data including logs and memory!
#          Backup important data before running.
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
INSTALL_USER="nomad"
INSTALL_DIR="/opt/nomad"
SERVICE_FILES=("nomad-backend.service" "nomad-tui@.service")

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}🗑️  Nomad Production Uninstallation${NC}"
echo "===================================="
echo ""
echo -e "${RED}WARNING: This will remove all Nomad data!${NC}"
echo "  - Application files in $INSTALL_DIR"
echo "  - All logs, memory, and sandbox data"
echo "  - Systemd services"
echo "  - System user '$INSTALL_USER'"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# --- Step 1: Stop and Disable Services ---
echo -e "${YELLOW}🛑 Stopping services...${NC}"

for service_file in "${SERVICE_FILES[@]}"; do
    service_name=$(basename "$service_file")
    
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        systemctl stop "$service_name"
        echo -e "${GREEN}✅ Stopped $service_name${NC}"
    fi
    
    if systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
        systemctl disable "$service_name"
        echo -e "${GREEN}✅ Disabled $service_name${NC}"
    fi
done

# --- Step 2: Remove Systemd Service Files ---
echo ""
echo -e "${YELLOW}🗑️  Removing systemd services...${NC}"

for service_file in "${SERVICE_FILES[@]}"; do
    if [ -f "/etc/systemd/system/$service_file" ]; then
        rm "/etc/systemd/system/$service_file"
        echo -e "${GREEN}✅ Removed $service_file${NC}"
    fi
done

systemctl daemon-reload
echo -e "${GREEN}✅ Systemd reloaded${NC}"

# --- Step 3: Backup Data (Optional) ---
echo ""
read -p "Do you want to backup data before deletion? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    BACKUP_DIR="/tmp/nomad-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}📦 Creating backup in $BACKUP_DIR...${NC}"
        
        # Backup important directories
        [ -d "$INSTALL_DIR/memory" ] && cp -r "$INSTALL_DIR/memory" "$BACKUP_DIR/"
        [ -d "$INSTALL_DIR/logs" ] && cp -r "$INSTALL_DIR/logs" "$BACKUP_DIR/"
        [ -f "$INSTALL_DIR/.env" ] && cp "$INSTALL_DIR/.env" "$BACKUP_DIR/"
        [ -d "$INSTALL_DIR/config" ] && cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/"
        
        echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
    fi
fi

# --- Step 4: Remove Installation Directory ---
echo ""
echo -e "${YELLOW}🗑️  Removing installation directory...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✅ Removed $INSTALL_DIR${NC}"
else
    echo -e "${YELLOW}⚠️  Directory $INSTALL_DIR not found${NC}"
fi

# --- Step 5: Remove System User ---
echo ""
read -p "Do you want to remove system user '$INSTALL_USER'? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if id "$INSTALL_USER" &>/dev/null; then
        userdel "$INSTALL_USER" 2>/dev/null || true
        echo -e "${GREEN}✅ Removed user '$INSTALL_USER'${NC}"
    else
        echo -e "${YELLOW}⚠️  User '$INSTALL_USER' not found${NC}"
    fi
fi

# --- Completion ---
echo ""
echo "=============================================="
echo -e "${GREEN}✅ Uninstallation Complete!${NC}"
echo "=============================================="
echo ""

if [[ -n "$BACKUP_DIR" ]] && [[ -d "$BACKUP_DIR" ]]; then
    echo "Backup saved to: $BACKUP_DIR"
    echo ""
fi

echo "Nomad has been removed from your system."
echo ""
