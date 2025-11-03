#!/bin/bash
# 🚀 SOPHIA SCI-FI TERMINAL LAUNCHER
# Launch Sophia with cyberpunk aesthetics

clear

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     🌌  SOPHIA HOLOGRAPHIC INTERFACE  🌌                  ║"
echo "║                                                           ║"
echo "║     Choose your reality:                                  ║"
echo "║                                                           ║"
echo "║     [1] 🎨 Rich Console - Quick & Beautiful               ║"
echo "║     [2] 🌟 Holographic TUI - Full Immersion               ║"
echo "║     [3] 🤖 Classic Mode - Traditional Terminal            ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
read -p "Select interface [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🎨 Launching Rich Console Interface..."
        echo ""
        python plugins/interface_terminal_scifi.py
        ;;
    2)
        echo ""
        echo "🌟 Initializing Holographic TUI..."
        echo ""
        textual run plugins/interface_terminal_holographic.py
        ;;
    3)
        echo ""
        echo "🤖 Starting Classic Interface..."
        echo ""
        export SOPHIA_SCIFI_MODE=false
        python run.py
        ;;
    *)
        echo "Invalid choice. Defaulting to Rich Console..."
        python plugins/interface_terminal_scifi.py
        ;;
esac
