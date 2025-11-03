# 🚀 SOPHIA SCI-FI TERMINAL INTERFACES

Welcome to the future of AI interaction! Choose your cyberpunk reality:

---

## 🎨 **LEVEL 1: Rich Console** *(Recommended for most users)*

**Features:**
- ⚡ Lightning-fast startup
- 🌈 Neon color palette (Cyan, Magenta, Yellow)
- 📊 Live metrics dashboard
- 💬 Split-panel chat interface
- 💻 Syntax-highlighted code blocks
- 🎯 Perfect for quick interactions

**Launch:**
```bash
python plugins/interface_terminal_scifi.py
```

**Screenshot:**
```
   _____ ____  _____  _    _ _____          
  / ____|  _ \|  __ \| |  | |_   _|   /\    
 | (___ | |_) | |__) | |__| | | |    /  \   
  \___ \|  _ <|  ___/|  __  | | |   / /\ \  
  ____) | |_) | |    | |  | |_| |_ / ____ \ 
 |_____/|____/|_|    |_|  |_|_____/_/    \_\
                                             
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AUTONOMOUS AI CONSCIOUSNESS  ⚡ v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

╔═══ ⚡ NEURAL METRICS ⚡ ═══╗  ╔═══ 💭 CONSCIOUSNESS STREAM ═══╗
║ STATUS    ● ONLINE         ║  ║ [20:32:14] YOU: Hello!       ║
║ TOKENS    15,420           ║  ║ [20:32:15] SOPHIA: Greetings!║
║ COST      $0.0234          ║  ║                              ║
╚════════════════════════════╝  ╚══════════════════════════════╝
```

---

## 🌟 **LEVEL 2: Holographic TUI** *(Full Immersion)*

**Features:**
- 🖥️ Full-screen terminal UI
- ⌨️ Interactive text input
- 📊 Multi-panel dashboard
- 🔄 Real-time system monitoring
- 🎮 Keyboard shortcuts (q=quit, c=clear, m=toggle)
- 🌌 Maximum cyberpunk aesthetics

**Launch:**
```bash
textual run plugins/interface_terminal_holographic.py
```

**Controls:**
- Type message + Enter = Send
- `q` = Quit
- `c` = Clear chat
- `m` = Toggle metrics panel

---

## 🤖 **LEVEL 3: Classic Mode** *(Traditional)*

**Features:**
- 📝 Simple text interface
- ⚡ Fastest performance
- 🔧 Minimal dependencies
- 🛠️ Best for automation/scripting

**Launch:**
```bash
export SOPHIA_SCIFI_MODE=false
python run.py
```

---

## 🎬 **Quick Launcher Script**

Use the interactive launcher to choose your interface:

```bash
./scripts/launch_scifi.sh
```

This will show a menu:
```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🌌  SOPHIA HOLOGRAPHIC INTERFACE  🌌                  ║
║                                                           ║
║     Choose your reality:                                  ║
║                                                           ║
║     [1] 🎨 Rich Console - Quick & Beautiful               ║
║     [2] 🌟 Holographic TUI - Full Immersion               ║
║     [3] 🤖 Classic Mode - Traditional Terminal            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📦 **Installation**

### Prerequisites

```bash
pip install rich textual textual-dev
```

### Verify Installation

```bash
# Test Rich Console
python -c "from rich.console import Console; Console().print('[bold cyan]✓ Rich installed![/bold cyan]')"

# Test Textual
textual --version
```

---

## 🎨 **Color Palette**

The interfaces use a cyberpunk-inspired neon palette:

| Color | Hex | Usage |
|-------|-----|-------|
| Neon Cyan | `#00FFFF` | Primary UI elements, borders |
| Neon Magenta | `#FF00FF` | Secondary highlights, chat |
| Neon Yellow | `#FFFF00` | User messages, warnings |
| Neon Green | `#00FF00` | Success states, status OK |
| Neon Blue | `#0080FF` | Metrics, counters |
| Neon Pink | `#FF69B4` | Accents |
| Neon Purple | `#9D00FF` | Special effects |
| Deep Space | `#0A0E27` | Background |

---

## 🔥 **Advanced Features**

### Real-time Metrics Tracking

The sci-fi interfaces automatically track:
- **Tokens used** - Total across all LLM calls
- **Cost** - Real-time $ tracking
- **Messages** - Conversation count
- **Response time** - Average AI response speed
- **Status** - System health indicator

### Event-Driven Updates

Interfaces listen to Sophia's Event Bus:
- `USER_INPUT` → Display user message
- `RESPONSE_GENERATED` → Display AI response + update metrics
- `ERROR` → Show holographic error panel
- `TASK_STARTED` → Show progress indicator

### Code Highlighting

Automatically detects and highlights code blocks:
```python
def example():
    return "✨ Beautiful syntax highlighting! ✨"
```

---

## 🎯 **Use Cases**

### For Daily Use
→ **Level 1 (Rich Console)** - Fast, beautiful, perfect balance

### For Demos & Presentations
→ **Level 2 (Holographic TUI)** - Maximum WOW factor

### For CI/CD & Automation
→ **Level 3 (Classic)** - Scriptable, minimal overhead

### For Development
→ **Level 1 + tmux** - Multiple panels, live monitoring

---

## 🌌 **Inspiration**

These interfaces are inspired by:
- 🎮 **Cyberpunk 2077** - Neon aesthetics, holographic panels
- 🎬 **Blade Runner** - Futuristic terminals, dark atmosphere
- 🎥 **The Matrix** - Green cascading text, data streams
- 🖥️ **Modern CLI tools** - uv, Docker Desktop, k9s

---

## 🚀 **What's Next?**

Planned features:
- [ ] Voice synthesis for AI responses
- [ ] Animated typing effect (char-by-char streaming)
- [ ] Plugin status monitor panel
- [ ] Network activity visualization
- [ ] Custom color themes (Matrix green, Retro amber, etc.)
- [ ] Mouse support in TUI
- [ ] Sound effects (optional)

---

## 📝 **Troubleshooting**

### "ModuleNotFoundError: No module named 'rich'"
```bash
pip install rich textual
```

### "Command not found: textual"
```bash
pip install textual-dev
```

### Colors not displaying correctly
```bash
# Check terminal support
echo $TERM

# Should be: xterm-256color or similar
# If not, add to ~/.bashrc:
export TERM=xterm-256color
```

### Layout breaks on small terminals
Minimum terminal size: 80x24 characters
```bash
# Check current size
tput cols  # Should be ≥80
tput lines # Should be ≥24
```

---

## 🎊 **Credits**

- **Rich** by Will McGugan - https://github.com/Textualize/rich
- **Textual** by Textualize - https://github.com/Textualize/textual
- **Sophia AI** - Built with love by the Sophia team

---

**Ready to enter the matrix?** 🌌

```bash
./scripts/launch_scifi.sh
```

_"The future is already here — it's just not evenly distributed."_ - William Gibson
