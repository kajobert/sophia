# 🚀 SOPHIA Sci-Fi Terminal Interfaces

## Tři Sci-Fi Styly

SOPHIA nabízí **3 jedinečné sci-fi terminálové rozhraní**, každé s vlastní estetikou a atmosférou:

---

## 🌈 1. CYBERPUNK (Původní)

**Pro všechny fanoušky futuristického neonového designu**

### Design
- **Barevná paleta**: Cyan, Magenta, Yellow, Blue
- **Styl**: Neonové světla, futuristické UI
- **Inspirace**: Cyberpunk 2077, Blade Runner
- **Single-line status bar** s real-time metrikami

### Features
✅ Progress bars (UV/Docker style)  
✅ Multi-step progress (Docker layers)  
✅ Real-time text streaming (ChatGPT style)  
✅ Interactive styled input  
✅ Thinking spinner + status bar  
✅ Syntax highlighting  
✅ **Blinking cyan cursor ▌** for input  

### Spuštění
```bash
python plugins/interface_terminal_scifi.py
```

### Screenshot
```
╔═══════════════════════════════════════════════╗
║    SOPHIA v2.0 - AI CONSCIOUSNESS ONLINE      ║
╚═══════════════════════════════════════════════╝

● │ DeepSeek Chat │ 15,500tok │ $0.0234 │ 1msg │ 2.1s
```

---

## 🟢 2. MATRIX (Pro Roberta)

**"Follow the white rabbit..." 🐰**

### Design
- **Barevná paleta**: Green monochrome (#00FF00)
- **Styl**: Digital rain, Matrix code aesthetic
- **Inspirace**: The Matrix (1999)
- **Everything is green!**

### Features
✅ Green digital rain progress bars  
✅ Matrix code compilation steps  
✅ "Wake up Neo" style prompts  
✅ Glitch text effects  
✅ "Decoding the Matrix" spinner  
✅ Matrix-themed messages  
✅ **Blinking cursor ▌** for input prompts  
✅ Fixed header with live neural activity log  

### Spuštění
```bash
python plugins/interface_terminal_matrix.py
```

### Screenshot
```
⢀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⡀
⢸  WAKE UP, NEO...                           ⢸
⢸  THE MATRIX HAS YOU                        ⢸
⢸  FOLLOW THE WHITE RABBIT 🐰                 ⢸
⣸⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⡇

⚫ │ MATRIX-AI-v3.14 │ 1,500tok │ $0.0234 │ 1msg │ 2.1s
```

### Easter Eggs
- "There is no spoon" messages
- Red pill/blue pill references
- Neo, Morpheus, Trinity mentions
- Zion connection messages

---

## 🟡 3. STAR TREK LCARS (Pro Radka)

**"Make it so!" 🖖**

### Design
- **Barevná paleta**: Orange (#FF9900), Blue (#6699CC), Purple (#9999FF)
- **Styl**: LCARS interface (Library Computer Access/Retrieval System)
- **Inspirace**: Star Trek: The Next Generation
- **Starship computer aesthetic**

### Features
✅ LCARS-style progress bars (orange/blue)  
✅ Stardate timestamps  
✅ "Computer working..." animations  
✅ Warp core initialization  
✅ Red/Yellow alert systems  
✅ USS Sophia NCC-1701-AI branding  
✅ **Blinking orange cursor ▌** for LCARS input  

### Spuštění
```bash
python plugins/interface_terminal_startrek.py
```

### Screenshot
```
╔════════════════════════════════════════════════════╗
║  USS SOPHIA NCC-1701-AI                        ║
║  LCARS v24.3 - MAIN COMPUTER                   ║
║  STARDATE: 2025.11.03                          ║
╚════════════════════════════════════════════════════╝

● │ M-5 Multitronic Unit │ 1,500tok │ $0.0234 │ 1msg │ 2.1s
```

### Easter Eggs
- Stardate format: `YYYY.MMDD.HHMM`
- Dilithium crystal charging
- Warp speed references
- "Engage!" commands
- Captain Picard quotes

---

## 🎮 Interactive Launcher

**Nejjednodušší způsob spuštění:**

```bash
./scripts/launch_scifi_terminal.sh
```

Menu vám nabídne všechny 3 styly:

```
╔═══════════════════════════════════════════════════════╗
║    🚀  SOPHIA SCI-FI TERMINAL LAUNCHER  🚀           ║
╚═══════════════════════════════════════════════════════╝

Vyberte si svůj sci-fi styl:

  1) 🌈  CYBERPUNK   - Neon colors, futuristic (původní)
  2) 🟢  MATRIX      - Green digital rain (pro Roberta)
  3) 🟡  STAR TREK   - LCARS orange/blue (pro Radka)

Vaše volba [1-3]: _
```

---

## 🎨 Barevné Palety

### CYBERPUNK
```python
{
    'primary': '#00FFFF',    # Cyan
    'secondary': '#FF00FF',  # Magenta
    'tertiary': '#FFFF00',   # Yellow
    'accent': '#0080FF',     # Blue
}
```

### MATRIX
```python
{
    'primary': '#00FF00',    # Matrix Green
    'secondary': '#008F00',  # Dark Green
    'tertiary': '#00FF41',   # Bright Green
    'bg': '#000000',         # Black
}
```

### STAR TREK
```python
{
    'primary': '#FF9900',    # LCARS Orange
    'secondary': '#9999FF',  # LCARS Purple
    'tertiary': '#CC6699',   # LCARS Pink
    'blue': '#6699CC',       # LCARS Blue
}
```

---

## 📊 Porovnání

| Feature | Cyberpunk | Matrix | Star Trek |
|---------|-----------|--------|-----------|
| **Progress Bars** | ✅ Neon | ✅ Green | ✅ Orange/Blue |
| **Streaming Text** | ✅ ChatGPT style | ✅ Digital rain | ✅ Computer voice |
| **Status Bar** | ✅ Single line | ✅ Single line | ✅ Single line |
| **Themed Prompts** | ✅ Futuristic | ✅ Neo/Morpheus | ✅ Picard/Crew |
| **Alert System** | ✅ Standard | ✅ Green only | ✅ Red/Yellow |
| **Code Display** | ✅ Neon borders | ✅ Green borders | ✅ Orange borders |
| **Spinner** | ✅ Dots | ✅ Matrix chars | ✅ Computer working |
| **Timestamps** | ✅ HH:MM:SS | ✅ HH:MM:SS | ✅ Stardate |

---

## 🚀 Use Cases

### CYBERPUNK - Pro každodenní použití
- ✅ Všestranný, moderní design
- ✅ Skvělá čitelnost
- ✅ Professional look
- ✅ UV/Docker inspired

### MATRIX - Pro hardcore kodéry
- ✅ Minimal distractions (jen zelená!)
- ✅ Hackerská atmosféra
- ✅ "Digital zen" mode
- ✅ Ideální pro noční coding sessions

### STAR TREK - Pro Star Trek fanoušky
- ✅ Nostalgická LCARS estetika
- ✅ Profesionální starship interface
- ✅ Skvělé pro prezentace
- ✅ "Make it so!" motivace

---

## 🔧 Technické Detaily

### Závislosti
```bash
pip install rich  # Všechny 3 styly používají Rich library
```

### Integrace do SOPHIA
Všechny 3 interface pluginy implementují stejné API:

```python
from plugins.interface_terminal_scifi import InterfaceTerminalSciFi
from plugins.interface_terminal_matrix import InterfaceTerminalMatrix
from plugins.interface_terminal_startrek import InterfaceTerminalStarTrek

# Vyberte si jeden:
interface = InterfaceTerminalStarTrek()
interface.setup({})

# Použití:
interface.display_message("SOPHIA", "Live long and prosper!")
interface.display_progress()  # Returns Progress object
interface.stream_text_async("Engage!")
```

### Plugin Properties
```python
@property
def name(self) -> str:
    return "interface_terminal_[cyberpunk|matrix|startrek]"

@property
def plugin_type(self) -> str:
    return "interface"

@property
def version(self) -> str:
    return "1.0.0"
```

---

## 🎬 Demo

Každý terminál má zabudované demo:

```bash
# Cyberpunk demo
python plugins/interface_terminal_scifi.py

# Matrix demo
python plugins/interface_terminal_matrix.py

# Star Trek demo
python plugins/interface_terminal_startrek.py
```

Demo ukazuje všech 5-7 hlavních features v akci!

---

## 🌟 Pro Tým

- **Robert**: Matrix verze čeká! 🟢 Follow the white rabbit!
- **Radek**: Star Trek LCARS je ready! 🟡 Make it so!
- **Všichni ostatní**: Cyberpunk je default! 🌈 Maximum WOW!

---

## 📝 Credits

- **Design**: Inspirováno Matrix (1999), Star Trek TNG (1987), Cyberpunk 2077
- **Implementation**: SOPHIA AI Team
- **Library**: Rich by Will McGugan
- **Style Patterns**: UV package manager, Docker CLI

---

**Live long and prosper!** 🖖
