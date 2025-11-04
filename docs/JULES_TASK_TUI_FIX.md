# 🤖 Jules Task: TUI UX Fix Implementation
**Assigned to:** Jules (Google AI Coding Agent)  
**Branch:** `nomad/tui-uv-style-fix`  
**Estimated tokens:** ~50,000 (complex task)  
**Priority:** HIGH  

---

## 📋 **Task Description**

Fix the Sophia TUI (Terminal User Interface) to achieve **UV/Docker style** with:
- ✅ NO flicker/blink during updates
- ✅ Sticky bottom panel for logs (stays fixed)
- ✅ Scrollable top panel for conversation
- ✅ Clean startup (no duplicate boot sequences)
- ✅ Proper stdout/stderr redirection

---

## 🎯 **Acceptance Criteria**

1. **Visual Output:**
   ```
   ╭──────────────── 💬 CONVERSATION ────────────────╮
   │ ╭─ [22:45:10] 👤 YOU                            │
   │ │ Hello Sophia!                                 │
   │ ╰─                                              │
   │                                                 │
   │ ╭─ [22:45:12] 🤖 SOPHIA                         │
   │ │ Hello! How can I assist you today?           │
   │ ╰─                                              │
   │                                                 │
   │ [scrollable conversation history]              │
   ╰─────────────────────────────────────────────────╯
   ╭───────────────── ⚙️ System Activity ────────────╮
   │   ⚙️ Task classified as 'simple_query'          │
   │   ⚙️ Calling LLM 'gemini-2.0-flash-001'         │
   │   ⚙️ Response received successfully             │
   │                                                 │
   │ [FIXED at bottom - last 10 log entries]        │
   ╰─────────────────────────────────────────────────╯
   ```

2. **Technical Requirements:**
   - ✅ No flicker (manual refresh only, not auto)
   - ✅ Bottom panel stays fixed when top scrolls
   - ✅ Boot sequence runs only ONCE
   - ✅ All print() and logging goes to panels (not stdout)
   - ✅ Works in both interactive and non-interactive mode

3. **Testing:**
   - ✅ `python run.py "test message"` - no flicker
   - ✅ `python run.py` - interactive typing works
   - ✅ Long conversation (30+ msgs) - scrolling smooth
   - ✅ No duplicate boot logos

---

## 📂 **Files to Modify**

### **Primary:**
1. **`plugins/interface_terminal_scifi.py`** (main TUI logic)
   - Fix Live mode: `auto_refresh=False`, manual refresh only
   - Add stdout/stderr capture
   - Fix duplicate boot with flag
   - Ensure callbacks work

2. **`core/scifi_logging.py`** (logging handler)
   - Already has rate limiting - verify it works
   - Ensure Panel updates don't print to stdout

3. **`core/kernel.py`** (already fixed - verify)
   - Interface execute() called in non-interactive mode ✅

### **Optional:**
4. **`run.py`** (startup)
   - Suppress warnings before Live mode starts

---

## 🔧 **Implementation Guide**

### **Step 1: Fix Flicker (CRITICAL)**

**File:** `plugins/interface_terminal_scifi.py`

**Current Code (line ~207):**
```python
self._live = Live(
    self._layout,
    console=self.console,
    refresh_per_second=1,  # Still auto-refreshing!
    screen=False,
    auto_refresh=False,  # Good!
    transient=False
)
```

**Required Change:**
```python
# UV Style: ZERO auto-refresh, manual updates ONLY
self._live = Live(
    self._layout,
    console=self.console,
    refresh_per_second=0,  # Disable auto-refresh completely
    screen=False,
    auto_refresh=False,
    transient=False,
    redirect_stdout=False,  # We'll handle stdout manually
    redirect_stderr=False
)
```

**Then add manual refresh after EVERY content update:**
```python
def display_message(self, role: str, content: str):
    # ... update layout ...
    self._layout["main"].update(main_panel)
    
    # CRITICAL: Manual refresh!
    if self._live and self._live.is_started:
        self._live.refresh()

def update_log_display(self, log_buffer=None):
    # ... update layout ...
    self._layout["logs"].update(log_panel)
    
    # CRITICAL: Manual refresh!
    if self._live and self._live.is_started:
        self._live.refresh()
```

---

### **Step 2: Redirect stdout/stderr (CRITICAL)**

**Problem:** print() and logging bypass Live display and break layout.

**Solution:** Capture stdout/stderr and redirect to log panel.

**Add to `interface_terminal_scifi.py`:**
```python
import sys
from io import StringIO

class OutputCapture:
    """Captures stdout/stderr and redirects to Live display."""
    
    def __init__(self, interface):
        self.interface = interface
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def write(self, text):
        """Redirect print() to log panel."""
        if text.strip():
            # Send to logging system instead of stdout
            logger.info(text.strip())
    
    def flush(self):
        pass
    
    def start(self):
        sys.stdout = self
        sys.stderr = self
    
    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

# In setup():
def setup(self, config: dict):
    # ... existing setup ...
    
    # Start Live mode
    self._start_live_mode()
    
    # CRITICAL: Capture stdout/stderr AFTER Live starts!
    self._output_capture = OutputCapture(self)
    self._output_capture.start()

# In cleanup():
def cleanup(self):
    if hasattr(self, '_output_capture'):
        self._output_capture.stop()
    self._stop_live_mode()
```

---

### **Step 3: Fix Duplicate Boot**

**File:** `plugins/interface_terminal_scifi.py`

**Current Issue:** Boot sequence runs 3 times during startup.

**Fix:**
```python
def setup(self, config: dict):
    # Skip if already initialized
    if self._booted:
        logger.debug("Skipping duplicate boot")
        return
    
    # Show boot ONCE
    self._show_boot_sequence_simple()
    self._booted = True
    
    # ... rest of setup ...
```

---

### **Step 4: Suppress Startup Warnings**

**File:** `run.py` (before kernel init)

**Add at top of main():**
```python
import warnings
warnings.filterwarnings("ignore", message="Langfuse.*")
warnings.filterwarnings("ignore", message="Authentication error.*")
warnings.filterwarnings("ignore", module="chromadb")
```

**Or redirect warnings to logging:**
```python
import logging
logging.captureWarnings(True)
```

---

### **Step 5: Verify Callback System**

**File:** `plugins/interface_terminal_scifi.py`

**Current code should work - verify:**
```python
async def execute(self, *, context: SharedContext) -> SharedContext:
    # Register callback in LISTENING phase
    if context.current_state == "LISTENING":
        context.payload["_response_callback"] = self._handle_response
    
    # Display user message
    if context.user_input:
        self.display_message("user", context.user_input)
    
    return context

def _handle_response(self, response: str):
    """Called by kernel when response ready."""
    self.display_message("assistant", response)
```

**File:** `core/kernel.py` (line ~197 - already fixed!)
```python
if single_run_input:
    context.user_input = single_run_input
    self.is_running = False
    
    # Call interface to register callbacks ✅
    interface_plugins = self.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
    for plugin in interface_plugins:
        await plugin.execute(context=context)
```

---

## 🧪 **Testing Checklist**

**Non-Interactive Mode:**
```bash
python run.py "hello world"
```
Expected:
- ✅ Single boot sequence
- ✅ Two panels visible (conversation + logs)
- ✅ User message appears in top panel
- ✅ Sophia response appears in top panel
- ✅ Log entries appear in bottom panel
- ✅ NO flicker/blink
- ✅ NO duplicate output

**Interactive Mode:**
```bash
python run.py
# Type: "hello sophia"
# Type: "what's 2+2?"
# Press Ctrl+C
```
Expected:
- ✅ Panels update smoothly
- ✅ Keyboard input works
- ✅ Conversation history scrolls
- ✅ Logs stay at bottom
- ✅ Clean exit

**Long Conversation:**
```bash
for i in {1..50}; do
  echo "Message $i" | python run.py 2>&1
done
```
Expected:
- ✅ No flicker after 50 iterations
- ✅ Layout stays intact
- ✅ No memory leaks

---

## 📦 **Deliverables**

1. **Fixed Files:**
   - `plugins/interface_terminal_scifi.py`
   - `core/scifi_logging.py` (if needed)
   - `run.py` (warnings suppression)

2. **Git Commit:**
   - Branch: `nomad/tui-uv-style-fix`
   - Commit msg: `fix(tui): UV-style smooth updates, no flicker, sticky panels`
   - Create PR to: `feature/jules-api-integration` (NOT master!)

3. **Test Results:**
   - Screenshot or video showing:
     - No flicker
     - Sticky bottom panel
     - Clean startup
     - Working conversation

4. **Documentation:**
   - Update `docs/TUI_UX_FIX_PLAN.md` with "COMPLETED" status

---

## ⚠️ **Important Notes**

1. **DO NOT merge to master** - PR to feature branch only!
2. **Test thoroughly** - all 3 test scenarios above
3. **Keep changes minimal** - only fix the flicker/layout issues
4. **Preserve functionality** - don't break existing features
5. **Follow existing code style** - match current patterns

---

## 🎓 **Reference Materials**

**Existing Implementation:**
- Layout setup: `interface_terminal_scifi.py` line ~115
- Live mode: `interface_terminal_scifi.py` line ~201
- Logging: `core/scifi_logging.py`
- Kernel integration: `core/kernel.py` line ~197

**Rich Library Docs:**
- Live Display: https://rich.readthedocs.io/en/latest/live.html
- Layout: https://rich.readthedocs.io/en/latest/layout.html
- Panel: https://rich.readthedocs.io/en/latest/panel.html

**UV Style Reference:**
- UV installer uses: manual refresh, transient progress, sticky panels
- Docker logs use: fixed bottom panel, scrollable main output

---

## 🚀 **Success Metrics**

- ✅ Zero flicker during normal operation
- ✅ Startup time < 2 seconds
- ✅ Memory stable (no leaks)
- ✅ Passes all 3 test scenarios
- ✅ Code review approved by Robert/Sophia

---

**Estimated Completion Time:** 2-4 hours  
**Token Budget:** ~50,000 tokens (Gemini 2.5 Pro)  
**Session Limit:** 1 session (out of 100/day)  

---

**Status:** 🟡 Ready for Jules Assignment  
**Next Action:** Create Jules session with this task
