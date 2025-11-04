# 🎨 TUI UX Fix - UV Style Implementation Plan
**Datum:** 2025-11-03  
**Problém:** Blikání, duplicitní boot, layout se neaktualizuje  
**Cíl:** UV/Docker style sticky panels bez flickeru  

---

## 🐛 **Root Cause Analysis**

### **Problémy zjištěné:**

1. **❌ Blikání (Flicker)**
   - Příčina: `auto_refresh=True` + `refresh_per_second=4`
   - UV používá: manual refresh pouze při změně obsahu

2. **❌ Layout se neaktualizuje**
   - Příčina: Standard logging přepisuje Live display
   - Řešení: Přesměrovat ALL output do Layout panelů

3. **❌ Duplicitní boot sequence (3x)**
   - Příčina: Plugin se inicializuje 3x během startupu
   - Řešení: Flag pro jednorázový boot

4. **❌ Callback se nevolá**
   - Příčina: V non-interactive módu kernel přeskakuje interface
   - Řešení: FIXED - kernel nyní volá interface i v single_run módu

5. **❌ WARNING zprávy ruší UX**
   - Příčina: Langfuse/chromadb warnings před Live startem
   - Řešení: Suppress warnings nebo přesměrovat do logs

---

## ✅ **Správné UV Implementace**

### **UV Principles:**
1. **No Auto-Refresh** - update pouze při změně obsahu
2. **Sticky Bottom Panel** - logs zůstávají fixní
3. **Smooth Updates** - žádné blikání, in-place přepis
4. **Transient Output** - progress bary mizí po dokončení
5. **Clean Separation** - main content scrolluje, logs ne

---

## 🔧 **Implementation Plan**

### **Phase 1: Fix Live Mode ✅ DONE**
- [x] `auto_refresh=False` - manual updates only
- [x] `refresh_per_second=1` - safety fallback
- [x] Manual `self._live.refresh()` po každé změně

### **Phase 2: Fix Callback System ✅ DONE**
- [x] Kernel volá interface i v non-interactive módu
- [x] Callback registrace v LISTENING fázi
- [x] `display_message()` volá se pro user i assistant

### **Phase 3: Redirect ALL Output 🚧 TODO**

**Problem:** Standard print() a logging přepisují Live display

**Solution:**
```python
# 1. Capture stdout/stderr
import sys
from io import StringIO

class LiveCapture:
    def __init__(self, live_display):
        self._live = live_display
        self._buffer = StringIO()
    
    def write(self, text):
        # Redirect to log panel instead of stdout
        if text.strip():
            self._live.update_logs(text)
    
    def flush(self):
        pass

# 2. Install capture at startup
sys.stdout = LiveCapture(interface._live)
sys.stderr = LiveCapture(interface._live)
```

### **Phase 4: Fix Duplicitní Boot 🚧 TODO**

**Problem:** Boot sequence runs 3x

**Root Cause:**
- 1x: Plugin __init__ při loading
- 2x: Plugin setup() při registration  
- 3x: Live mode start

**Solution:**
```python
def setup(self, config: dict):
    if self._booted:
        return  # Skip duplicate boot
    
    self._booted = True
    self._show_boot_sequence_simple()
    # ... rest of setup
```

### **Phase 5: Suppress Warnings 🚧 TODO**

**Option A:** Filter warnings
```python
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Langfuse.*")
```

**Option B:** Redirect warnings to logs
```python
import logging
logging.captureWarnings(True)
```

**Option C:** Show warnings in log panel (best UX)
```python
# Warnings go to sticky bottom panel, not main output
```

---

## 🎯 **Final Target UX**

```
╭────────────────────── 💬 CONVERSATION ──────────────────────╮
│ ╭─ [22:30:42] 👤 YOU                                        │
│ │ hello world, no more flicker!                             │
│ ╰─                                                           │
│                                                              │
│ ╭─ [22:30:45] 🤖 SOPHIA                                     │
│ │ Hello world! 🌍✨ It's wonderful to connect with you.     │
│ │ The statement "no more flicker" symbolizes stability      │
│ │ and clarity. Let's embrace this as an affirmation!        │
│ ╰─                                                           │
│                                                              │
│ [40 lines of scrollable conversation history]               │
╰──────────────────────────────────────────────────────────────╯
╭──────────────────── ⚙️ System Activity ─────────────────────╮
│   ⚙️ Task classified as 'simple_query'                       │
│   ⚙️ Calling LLM 'gemini-2.0-flash-001'                      │
│   ⚙️ LLM response received successfully                      │
│   ⚙️ Saved interaction to memory                             │
│   ⚙️ Consciousness loop finished                             │
│                                                              │
│ [10 lines fixed - newest logs at bottom]                    │
╰──────────────────────────────────────────────────────────────╯
```

**Characteristics:**
- ✅ NO flicker - smooth in-place updates
- ✅ Top panel scrolls with conversation
- ✅ Bottom panel stays fixed (sticky)
- ✅ Colored logs (cyan ⚙️ icons)
- ✅ Rounded borders (UV aesthetic)
- ✅ Clean - no duplicate output
- ✅ Fast - manual refresh only when needed

---

## 📋 **Remaining Tasks**

### **Critical (Blocking):**
- [ ] **Redirect stdout/stderr** - prevent print() from breaking layout
- [ ] **Test in interactive mode** - verify keyboard input works
- [ ] **Fix logging overlap** - logs should update panel, not print

### **Important (UX):**
- [ ] **Fix duplicate boot** - show logo only once
- [ ] **Suppress warnings** - Langfuse/chromadb noise
- [ ] **Add status LEDs** - power/cpu/network indicators

### **Nice-to-have:**
- [ ] **Progress bars** - transient for long tasks
- [ ] **Typing indicator** - when Sophia is thinking
- [ ] **Keyboard shortcuts** - Ctrl+C graceful exit

---

## 🧪 **Testing Checklist**

- [ ] Non-interactive mode: `python run.py "test"`
- [ ] Interactive mode: `python run.py` (type manually)
- [ ] Long conversation (30+ messages) - scrolling works
- [ ] Multiple log entries - sticky panel updates correctly
- [ ] Ctrl+C exit - cleanup Live mode properly
- [ ] No flicker visible during updates
- [ ] No duplicate boot sequences
- [ ] No WARNING spam in output

---

## 🚀 **Next Steps**

1. ✅ **Create this plan** - done!
2. 🚧 **Fix stdout redirect** - capture print() calls
3. 🚧 **Fix duplicate boot** - add flag check
4. 🚧 **Test interactive mode** - verify everything works
5. ⏳ **Suppress warnings** - clean startup
6. ⏳ **Commit & merge** - ship it!

---

**Status:** 🟡 In Progress - Core fixes done, cleanup needed
