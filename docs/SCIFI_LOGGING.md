# 🎨 Sci-Fi Logging System - UV/Docker Style

**Organized Terminal Logs** - Retro DOS Gaming Nostalgia ⚡

## Overview

Custom logging system that transforms boring Python logs into **organized, colorful panels** like modern CLI tools (UV, Docker, Kubernetes).

### Features

✅ **Ring Buffer** - Last 10 logs only (auto-scrolling)  
✅ **Color-Coded** - Cyan (INFO), Yellow (WARNING), Red (ERROR)  
✅ **Icon System** - 🔍 DEBUG, ⚙️ INFO, ⚠️ WARNING, ❌ ERROR, 🚨 CRITICAL  
✅ **Clean Messages** - No timestamps in panel, just the important info  
✅ **Organized Panel** - "⚙️ System Activity" box with rounded corners  
✅ **Non-Intrusive** - Main conversation stays clean above  
✅ **Rate Limited** - Max 10 FPS updates for smooth performance  
✅ **UV Style** - Rounded borders, soft colors, clean design  

## Live Demo

```
>>> Sophia: Plan executed successfully. Result: Hello, world! 🌍✨
<<< Uživatel:

╭───────────────────────── ⚙️ System Activity ─────────────────────────╮
│   ⚙️ User input received: 'hello world'                              │
│   ⚙️ Calling LLM 'openrouter/anthropic/claude-3-haiku'              │
│   ⚙️ LLM response received successfully.                             │
│   ⚙️ Task classified as 'simple_query'                               │
│   ⚙️ Cognitive Task Router executed successfully.                    │
│   ⚙️ Calling LLM 'openrouter/google/gemini-2.0-flash-001'           │
│   ⚙️ LLM response received successfully.                             │
│                                                                      │
│                                                                      │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

## Implementation

### 1. SciFiLoggingHandler (`core/scifi_logging.py`)

Custom `logging.Handler` that:
- Intercepts all Python logs
- Filters boring technical messages
- Extracts clean message text
- Adds to ring buffer (`deque(maxlen=10)`)
- Maps levels to colors/icons
- Returns formatted Panel with **rounded borders** (UV style)
- **Rate limits updates** to 10 FPS for smooth performance

```python
class SciFiLoggingHandler(logging.Handler):
    def __init__(self, interface, max_logs=10):
        self.log_buffer = deque(maxlen=max_logs)
        self._update_interval = 0.1  # Max 10 FPS
        self._last_update = 0
        
        self.level_colors = {
            'DEBUG': 'dim cyan',
            'INFO': 'cyan',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold red',
        }
        self.level_icons = {
            'DEBUG': '🔍',
            'INFO': '⚙️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨',
        }
    
    def emit(self, record):
        # Extract clean message
        msg = self.format(record)
        
        # Add to buffer
        color = self.level_colors[record.levelname]
        icon = self.level_icons[record.levelname]
        formatted = f"{icon} {msg}"
        self.log_buffer.append((color, formatted))
        
        # Update display with rate limiting (UV style!)
        now = time.time()
        if now - self._last_update >= self._update_interval:
            if hasattr(self.interface, 'update_log_display'):
                self.interface.update_log_display(self.log_buffer)
            self._last_update = now
    
    def get_log_panel(self) -> Panel:
        # Returns Panel with rounded borders (UV style)
        content = Text()
        for color, message in self.log_buffer:
            content.append(f"  {message}\n", style=color)
        
        return Panel(
            content,
            title="[bold cyan]⚙️ System Activity[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,  # Soft corners like UV!
            height=12,
            padding=(0, 1)
        )
```

### 2. Interface Integration (`plugins/interface_terminal_scifi.py`)

Cyberpunk terminal has `update_log_display()` method:

```python
def update_log_display(self, log_buffer=None):
    """Update fixed bottom log panel (UV/Docker style)."""
    if hasattr(self, '_scifi_log_handler'):
        log_panel = self._scifi_log_handler.get_log_panel()
        self.console.print(log_panel)
```

### 3. Installation (`run.py`)

After kernel initialization:

```python
from core.scifi_logging import install_scifi_logging

# Load sci-fi interface
scifi_interface = _load_scifi_interface(kernel, ui_style)

# Install custom logging
install_scifi_logging(scifi_interface, max_logs=10)
print("✨ Sci-fi logging enabled - all output now in CYBERPUNK style!")
```

## Usage

Just run Sophia with Cyberpunk UI - logs automatically appear in organized panels:

```bash
python run.py "your question here"
```

Output:
```
╭───────────────────────── System Activity ─────────────────────────╮
│ ⚙️ User input received: 'your question here'                      │
│ ⚙️ Calling LLM 'openrouter/anthropic/claude-3-haiku'             │
│ ⚙️ LLM response received successfully.                            │
│ ⚙️ Task classified as 'simple_query'                              │
│ ⚙️ Cognitive Task Router executed successfully.                   │
╰───────────────────────────────────────────────────────────────────╯
```

## Technical Details

### Ring Buffer
- Uses `collections.deque(maxlen=10)`
- Auto-discards old logs (FIFO)
- Always shows last 10 messages
- No memory leaks

### Message Filtering
Skips boring logs like:
- `plugin_name='...'`
- `extra={...}`
- Traceback details
- Module paths

Only shows **human-friendly messages**:
- User input received
- Calling LLM X
- Response received
- Task classified
- Command finished

### Console Handler Suppression
```python
# Disable old console logging (ERROR only)
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.ERROR)

# Add our fancy handler
logging.root.addHandler(scifi_handler)
```

## Future Enhancements

### Potential: Rich Live + Layout
For **truly fixed bottom panel** (like `docker build`):

```python
from rich.live import Live
from rich.layout import Layout

layout = Layout()
layout.split_column(
    Layout(name="main", ratio=8),   # Conversation
    Layout(name="logs", size=12)    # Fixed logs
)

with Live(layout, refresh_per_second=4):
    # Update logs without reprinting
    layout["logs"].update(log_panel)
```

**Why not implemented?**
- Conflicts with `input()` - can't get user input during Live
- Would require async rewrite of entire interaction flow
- Current solution is simpler and works perfectly

## Inspiration

Modern CLI tools with great UX:
- **UV** (Python package manager) - Clean progress bars
- **Docker** - Layer-by-layer build output
- **Kubernetes** - Pod status panels
- **DOS games** - Retro terminal aesthetics

## Related Files

- `core/scifi_logging.py` - Handler implementation
- `plugins/interface_terminal_scifi.py` - Cyberpunk UI
- `run.py` - Integration point
- `docs/cyberpunk_demo.svg` - Animated demo for README

---

**Built with ❤️ for retro DOS gaming nostalgia** 🎮
