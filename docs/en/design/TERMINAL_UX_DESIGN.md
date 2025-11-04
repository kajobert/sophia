# Terminal UX Design Specification

**Document:** Terminal Interface UX Improvements  
**Target:** `plugins/interface_terminal.py`  
**Version:** 2.0  
**Status:** Design Specification  
**Created:** November 3, 2025

---

## 🎯 Objectives

Transform Sophia's terminal interface from basic text I/O into a rich, informative, developer-friendly experience that provides real-time visibility into consciousness loop phases, active operations, and system state.

**Inspiration:** Modern CLI tools (htop, k9s, lazydocker), Rich library examples

---

## 📦 Technology Stack

### Primary Library: [Rich](https://github.com/Textualize/rich)
```bash
pip install rich
```

**Why Rich?**
- ✅ Advanced terminal formatting (colors, tables, panels, trees)
- ✅ Live displays and progress indicators
- ✅ Syntax highlighting for code
- ✅ Markdown rendering
- ✅ Emoji support
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Zero external dependencies

---

## 🎨 Design Components

### 1. Status Bar (Top)

**Fixed header showing current system state:**

```
╭─────────────────────────────────────────────────────────────────────────────╮
│ 🧠 SOPHIA V2 │ Phase: PLANNING │ Plugin: cognitive_planner │ Mem: 45MB/20GB │
│ Session: 7a3f │ Uptime: 2h 34m │ Tasks: 3 active │ Status: ● RUNNING     │
╰─────────────────────────────────────────────────────────────────────────────╯
```

**Elements:**
- **Consciousness Phase:** Color-coded current phase
  - 🎧 `LISTENING` (cyan)
  - 🧠 `PLANNING` (yellow)
  - ⚙️ `EXECUTING` (blue)
  - 💬 `RESPONDING` (green)
  - 💾 `MEMORIZING` (purple)
- **Active Plugin:** Currently executing plugin name
- **Memory Usage:** Current/Max (from autonomy.yaml)
- **Session ID:** First 4 chars for quick reference
- **Uptime:** Time since start
- **Task Queue:** Number of active background tasks
- **Status:** Running/Sleeping/Error (with indicator)

**Implementation:**
```python
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

def render_status_bar(context: SharedContext) -> Panel:
    phase_emoji = {
        "LISTENING": "🎧",
        "PLANNING": "🧠",
        "EXECUTING": "⚙️",
        "RESPONDING": "💬",
        "MEMORIZING": "💾"
    }
    
    phase_color = {
        "LISTENING": "cyan",
        "PLANNING": "yellow",
        "EXECUTING": "blue",
        "RESPONDING": "green",
        "MEMORIZING": "purple"
    }
    
    status_text = Text()
    status_text.append(f"{phase_emoji[context.phase]} SOPHIA V2", style="bold white")
    status_text.append(" │ ", style="dim")
    status_text.append(f"Phase: {context.phase}", style=f"bold {phase_color[context.phase]}")
    # ... rest of status bar
    
    return Panel(status_text, border_style="blue")
```

---

### 2. Message Types with Icons & Colors

**User Messages:**
```
👤 You (12:34:56)
Can you analyze the codebase?
```

**Sophia Responses:**
```
🤖 Sophia (12:35:02) [planning phase]
I'll analyze the codebase using cognitive_code_reader plugin.

[executing...]

✅ Analysis complete. Found 27 plugins across 4 categories:
• Interfaces: 2
• Tools: 15
• Cognitive: 7
• Memory: 2
```

**System Messages:**
```
ℹ️ System (12:35:10)
Background task started: Jules monitoring (ID: abc123)
```

**Error Messages:**
```
⚠️ Error (12:35:15)
Plugin execution failed: FileNotFoundError
See logs for details: logs/sophia_2025-11-03.log
```

**Debug Messages (if verbose mode):**
```
🔍 Debug (12:35:20)
LLM call: openrouter/anthropic/claude-3.5-sonnet
Tokens: 1,234 (prompt) + 567 (completion) = 1,801 total
Cost: $0.0234
```

**Color Scheme:**
- User: `cyan`
- Sophia: `green`
- System: `blue`
- Error: `red`
- Warning: `yellow`
- Debug: `dim`

---

### 3. Code & Log Formatting

**Code Blocks with Syntax Highlighting:**

````python
from rich.syntax import Syntax
from rich.console import Console

def display_code(code: str, language: str = "python"):
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)
````

**Example Output:**
```python
  1 │ async def consciousness_loop(self):
  2 │     """Main event-driven consciousness loop"""
  3 │     while self.running:
  4 │         await self.listen_for_events()
  5 │         # Process events...
```

**Log Display:**
```
╭─ Log Output ──────────────────────────────────────────────────────────────╮
│ [2025-11-03 12:34:56] INFO: Kernel initialized                           │
│ [2025-11-03 12:34:57] DEBUG: Loading 27 plugins                          │
│ [2025-11-03 12:34:58] INFO: Web UI started on http://localhost:8000      │
│ [2025-11-03 12:35:00] INFO: Entering consciousness loop                  │
╰───────────────────────────────────────────────────────────────────────────╯
```

---

### 4. Progress Indicators

**For Long-Running Tasks:**

**Simple Spinner:**
```
⠋ Analyzing codebase... (15 files processed)
```

**Progress Bar:**
```
Processing files ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 78/100 (78%) 2.5s
```

**Multi-Task Progress:**
```
╭─ Active Tasks ────────────────────────────────────────────────────────────╮
│ ● Jules Task #1: Code review      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45% 2m  │
│ ● Jules Task #2: Test generation  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 12% 5m  │
│ ● Memory consolidation             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 89% 30s │
╰───────────────────────────────────────────────────────────────────────────╯
```

**Implementation:**
```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
) as progress:
    task = progress.add_task("Analyzing...", total=100)
    for i in range(100):
        # Do work
        progress.update(task, advance=1)
```

---

### 5. Tables for Structured Data

**Plugin List:**
```
╭─────────────────────┬──────────┬──────────────────────────────────────╮
│ Plugin              │ Type     │ Description                          │
├─────────────────────┼──────────┼──────────────────────────────────────┤
│ interface_terminal  │ INTERFACE│ Terminal interaction                 │
│ interface_webui     │ INTERFACE│ Web UI interaction                   │
│ tool_file_system    │ TOOL     │ File I/O operations                  │
│ tool_bash           │ TOOL     │ Shell command execution              │
│ cognitive_planner   │ COGNITIVE│ Multi-step task planning             │
│ memory_sqlite       │ MEMORY   │ Short-term working memory            │
╰─────────────────────┴──────────┴──────────────────────────────────────╯
```

**Jules Task Status:**
```
╭─────┬──────────────┬──────────┬──────────┬─────────────────────╮
│ ID  │ Description  │ Status   │ Progress │ Started             │
├─────┼──────────────┼──────────┼──────────┼─────────────────────┤
│ a1b │ Code review  │ RUNNING  │ 45%      │ 2025-11-03 12:30:00 │
│ c2d │ Test gen     │ QUEUED   │ 0%       │ -                   │
│ e3f │ Refactor     │ COMPLETE │ 100%     │ 2025-11-03 11:00:00 │
╰─────┴──────────────┴──────────┴──────────┴─────────────────────╯
```

---

### 6. Live Dashboard (Optional)

**Full-screen live dashboard using Rich Layout:**

```
╭─ SOPHIA V2 DASHBOARD ─────────────────────────────────────────────────────╮
│                                                                            │
│ ┌─ Status ─────────────────────┐  ┌─ Consciousness Loop ──────────────┐  │
│ │ Phase: EXECUTING             │  │                                    │  │
│ │ Uptime: 2h 34m               │  │  1. LISTENING    ✓                 │  │
│ │ Memory: 45MB / 20GB          │  │  2. PLANNING     ✓                 │  │
│ │ Tasks: 3 active              │  │  3. EXECUTING    ← (current)       │  │
│ └──────────────────────────────┘  │  4. RESPONDING                     │  │
│                                    │  5. MEMORIZING                     │  │
│ ┌─ Active Tasks ───────────────┐  └────────────────────────────────────┘  │
│ │ ● Jules #a1b (45%) - 2m      │                                          │
│ │ ● Jules #c2d (queued)        │  ┌─ Recent Messages ─────────────────┐  │
│ │ ● Memory consolidation (89%) │  │ 👤 You: Analyze codebase          │  │
│ └──────────────────────────────┘  │ 🤖 Sophia: Starting analysis...   │  │
│                                    │ ℹ️ System: Task abc123 started    │  │
╰────────────────────────────────────┴────────────────────────────────────────╯

> _
```

**Activate with:** `--dashboard` flag or interactive command `!dashboard`

---

## 🔧 Configuration

### Settings in `config/settings.yaml`:

```yaml
terminal:
  ui_mode: "rich"  # "simple" | "rich" | "dashboard"
  theme: "dark"    # "dark" | "light"
  show_timestamps: true
  show_session_id: true
  emoji_enabled: true
  syntax_highlighting: true
  progress_indicators: true
  status_bar: true
  verbose_debug: false  # Show debug messages
  
  colors:
    user: "cyan"
    sophia: "green"
    system: "blue"
    error: "red"
    warning: "yellow"
    
  syntax_theme: "monokai"  # Any Pygments theme
```

---

## 📝 Implementation Plan

### Phase 1: Core Rich Integration (2-3 hours)
1. Add `rich` dependency to `requirements.in`
2. Create `core/rich_console.py` helper module
3. Refactor `interface_terminal.py` to use Rich Console
4. Implement basic colored output for message types

### Phase 2: Status Bar & Progress (2-3 hours)
1. Implement status bar rendering
2. Add context.phase tracking in kernel
3. Implement progress indicators for long tasks
4. Add spinner for async operations

### Phase 3: Code & Tables (2-3 hours)
1. Implement syntax highlighting for code blocks
2. Add table rendering for structured data
3. Improve log display formatting
4. Add panel borders for sections

### Phase 4: Dashboard (Optional, 4-6 hours)
1. Implement live layout system
2. Create dashboard components
3. Add keyboard shortcuts for navigation
4. Implement graceful fallback if terminal doesn't support

### Phase 5: Testing & Polish (2-3 hours)
1. Test on different terminal emulators
2. Add fallback for non-Rich terminals
3. Performance testing with large outputs
4. Documentation update

**Total Estimated Time:** 12-18 hours

---

## 🎯 Success Criteria

- ✅ Status bar shows real-time consciousness phase
- ✅ All message types have distinct icons and colors
- ✅ Code blocks display with syntax highlighting
- ✅ Progress indicators work for long tasks
- ✅ Tables render cleanly for structured data
- ✅ Graceful fallback for unsupported terminals
- ✅ Performance impact < 5% on message rendering
- ✅ User-configurable via settings.yaml

---

## 📚 References

- **Rich Documentation:** https://rich.readthedocs.io/
- **Rich Gallery:** https://github.com/Textualize/rich#rich-library
- **Textual (future):** https://github.com/Textualize/textual (for full TUI)

---

## Related Documentation

- [Technical Architecture](../03_TECHNICAL_ARCHITECTURE.md) - Plugin system
- [User Guide](../06_USER_GUIDE.md) - Current terminal usage
- [Web UI Redesign](WEBUI_REDESIGN.md) - Companion UI improvements

---

**Navigation:** [📚 Index](../INDEX.md) | [🎨 Design Docs](./README.md) | [🌐 Web UI Design](WEBUI_REDESIGN.md)

---

*Created: November 3, 2025 | Status: Design Specification | Implementation: Pending*
