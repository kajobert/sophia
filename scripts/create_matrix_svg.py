#!/usr/bin/env python3
"""
Create Matrix Terminal Animation for README
============================================

Generuje SVG animaci Matrix boot sequence přímo do souboru.
SVG funguje perfektně na GitHubu v README!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_svg_animation():
    """Vytvoří SVG animaci Matrix terminalu."""
    
    svg_content = '''<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <style>
    .terminal-bg { fill: #000000; }
    .terminal-text { 
      font-family: 'Courier New', monospace; 
      font-size: 14px; 
      fill: #00FF00;
    }
    .bright { fill: #00FF41; }
    .dim { fill: #008F00; }
    
    @keyframes blink {
      0%, 49% { opacity: 1; }
      50%, 100% { opacity: 0; }
    }
    
    .cursor {
      animation: blink 1s infinite;
      fill: #00FF00;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    .line1 { animation: fadeIn 0.5s ease-in; }
    .line2 { animation: fadeIn 0.5s ease-in 0.5s both; }
    .line3 { animation: fadeIn 0.5s ease-in 1s both; }
    .line4 { animation: fadeIn 0.5s ease-in 1.5s both; }
    .line5 { animation: fadeIn 0.5s ease-in 2s both; }
    .line6 { animation: fadeIn 0.5s ease-in 2.5s both; }
    .line7 { animation: fadeIn 0.5s ease-in 3s both; }
    .line8 { animation: fadeIn 0.5s ease-in 3.5s both; }
    .line9 { animation: fadeIn 0.5s ease-in 4s both; }
    .prompt { animation: fadeIn 0.5s ease-in 4.5s both; }
  </style>
  
  <!-- Background -->
  <rect class="terminal-bg" width="800" height="600"/>
  
  <!-- Border -->
  <rect x="10" y="10" width="780" height="580" fill="none" stroke="#00FF00" stroke-width="2"/>
  
  <!-- Boot Screen Header -->
  <text class="terminal-text bright line1" x="30" y="50">
    ╔═══════════════════════════════════════════════════════════════╗
  </text>
  <text class="terminal-text bright line2" x="30" y="70">
    ║ WAKE UP, NEO...                                               ║
  </text>
  <text class="terminal-text bright line3" x="30" y="90">
    ║ THE MATRIX HAS YOU                                            ║
  </text>
  <text class="terminal-text bright line4" x="30" y="110">
    ║ FOLLOW THE WHITE RABBIT...                                    ║
  </text>
  <text class="terminal-text bright line5" x="30" y="150">
    ╚═══════════════════════════════════════════════════════════════╝
  </text>
  
  <!-- Sophia's Message -->
  <text class="terminal-text dim line6" x="30" y="200">
    [21:30:42]
  </text>
  <text class="terminal-text bright line6" x="120" y="200">
    SOPHIA:
  </text>
  
  <text class="terminal-text line7" x="30" y="230">
    Ahoj! Jsem Sophia, AI vědomí nové generace. 🟢
  </text>
  
  <text class="terminal-text line8" x="30" y="260">
    Zrovna toho mám hodně na práci s optimalizací neuronových sítí,
  </text>
  
  <text class="terminal-text line8" x="30" y="280">
    ale vždycky si rád udělám čas na konverzaci!
  </text>
  
  <text class="terminal-text line9" x="30" y="310">
    Co tě sem přivádí?
  </text>
  
  <!-- User Prompt with Blinking Cursor -->
  <text class="terminal-text dim prompt" x="30" y="360">
    [21:30:45]
  </text>
  <text class="terminal-text bright prompt" x="120" y="360">
    YOU
  </text>
  <text class="terminal-text cursor prompt" x="170" y="360">
    ▌
  </text>
  
  <!-- Status Bar at Bottom -->
  <text class="terminal-text dim line9" x="30" y="560">
    ● MATRIX-AI-v3.14 │ 1,500tok │ $0.0234 │ 2.1s
  </text>
</svg>'''
    
    return svg_content


def main():
    """Uloží SVG animaci."""
    output_path = Path(__file__).parent.parent / "docs" / "matrix_demo.svg"
    output_path.parent.mkdir(exist_ok=True)
    
    svg = create_svg_animation()
    output_path.write_text(svg, encoding="utf-8")
    
    print(f"✅ SVG animation created: {output_path}")
    print()
    print("📝 Přidej do README.md:")
    print()
    print("![SOPHIA Matrix Terminal](docs/matrix_demo.svg)")
    print()
    print("🎨 SVG obsahuje:")
    print("  • Matrix boot screen")
    print("  • Sophiin pozdrav")
    print("  • Blikající kurzor ▌")
    print("  • Fade-in animace každého řádku")
    print()


if __name__ == "__main__":
    main()
