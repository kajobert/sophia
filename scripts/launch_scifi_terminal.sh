#!/bin/bash
# SOPHIA Sci-Fi Terminal Launcher
# Vyberte si svůj styl! 🚀

clear

echo "╔═══════════════════════════════════════════════════════╗"
echo "║                                                       ║"
echo "║    🚀  SOPHIA SCI-FI TERMINAL LAUNCHER  🚀           ║"
echo "║                                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Vyberte si svůj sci-fi styl:"
echo ""
echo "  1) 🌈  CYBERPUNK   - Neon colors, futuristic (původní)"
echo "  2) 🟢  MATRIX      - Green digital rain (pro Roberta)"
echo "  3) 🟡  STAR TREK   - LCARS orange/blue (pro Radka)"
echo ""
echo "  0) ❌  Zrušit"
echo ""
read -p "Vaše volba [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🌈 Spouštím CYBERPUNK terminal..."
        echo ""
        python plugins/interface_terminal_scifi.py
        ;;
    2)
        echo ""
        echo "🟢 Spouštím MATRIX terminal..."
        echo "   'Follow the white rabbit...' 🐰"
        echo ""
        python plugins/interface_terminal_matrix.py
        ;;
    3)
        echo ""
        echo "🟡 Spouštím STAR TREK LCARS terminal..."
        echo "   'Make it so!' 🖖"
        echo ""
        python plugins/interface_terminal_startrek.py
        ;;
    0)
        echo ""
        echo "Zrušeno."
        ;;
    *)
        echo ""
        echo "❌ Neplatná volba!"
        exit 1
        ;;
esac
