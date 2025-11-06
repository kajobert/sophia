# Personal Agent Notes (AGENTS_PERSONAL.md)

This file records runtime details, terminal usage, background jobs, and my local work patterns.

- Date created: 2025-11-05
- Workspace: c:\SOPHIA\sophia
- Branch: feature/year-2030-ami-complete

## Terminal policy
- Long-running commands (test runs, builds, servers) will be started in a new WSL terminal and run in the background.
- I will save outputs to log files (e.g., `full_test_run.log`) so they can be inspected asynchronously.
- When I start a background job I will record the terminal id and command here.

## Recent background jobs
- None yet.

### Background job: full test run (attempt 1)
- Terminal id: 18f6a82d-2c7e-4c9d-a5c3-6c4a28d73896
- Command: `cd /mnt/c/SOPHIA/sophia && .venv/Scripts/activate || true; pytest -q | tee full_test_run.log`
- Outcome: Failed to run — `pytest` not found in this shell. Suggest using the virtualenv Python executable instead: `.venv/bin/python -m pytest` on WSL.

Will retry using virtualenv Python in a new background terminal.

### Background job: full test run (attempt 2, verbose)
- Terminal id: 2d23e0b7-0568-4d82-b84f-98429c5d53e8
- Command: `cd /mnt/c/SOPHIA/sophia && .venv/bin/python -m pytest -vv | tee full_test_run_verbose.log`
- Log file: `full_test_run_verbose.log`
- Status: Running in background. I'll fetch the log when it finishes and summarize failures (if any).

## Notes about my environment and utilities
- Default shell: wsl.exe (WSL). Use `/mnt/c/...` paths for file operations.
- Virtualenv path used in this workspace: `.venv/` (activate with `.venv/Scripts/activate` on WSL/Windows).
- Test runner: `pytest` (run with `pytest -q`).

## Where I write state
- This file (`docs/AGENTS_PERSONAL.md`) is for private agent notes and is not a replacement for repository `AGENTS.md`.
- I will also update `WORKLOG.md` for formal changelog entries when changes are committed.

---

I'll append new entries here when I start background jobs, discover notable test failures, or change workflow behavior.

## 2025-11-06: Headless test debugging session

### Background job: headless test (run_single_plan_and_wait.py)
- Command: `PYTHONPATH=. .venv/bin/python3 scripts/run_single_plan_and_wait.py`
- Log file: `headless_test_output.log`
- Status: ✅ Completed, but with unexpected behavior

### Key lessons learned:

1. **Plugin initialization timing is critical**
   - Plugins are loaded and initialized in `PluginManager.__init__()` → `load_plugins()` → `_register_plugin()`
   - This happens BEFORE `kernel.initialize()` is called
   - Environment variables like `SOPHIA_DISABLE_INTERACTIVE_PLUGINS` must be set **before importing Kernel**
   - Modified `scripts/run_single_plan_and_wait.py` to set env vars at the top, before any imports

2. **Plugin initialization errors are non-fatal**
   - `InterfaceTerminalMatrix` throws error: `'interface'` (KeyError or missing dependency)
   - Error is caught in `plugin_manager.py:85` and logged, but process continues
   - Failed plugins are NOT added to the registry
   - This is actually good for headless mode - broken interactive plugins don't block execution

3. **Added SOPHIA_DISABLE_INTERACTIVE_PLUGINS support**
   - Modified `core/kernel.py` at line ~100 to filter out `PluginType.INTERFACE` plugins when env var is set
   - Filters happen in `initialize()` method, after initial plugin loading
   - Works similarly to existing `SOPHIA_FORCE_LOCAL_ONLY` pattern

4. **Unexpected behavior: self-diagnostic ran instead of custom plan**
   - Script provided `single_run_input` with explicit JSON plan to write `sandbox/headless_test.txt`
   - Kernel executed `core_self_diagnostic` instead and wrote `sandbox/self_diagnostic.json`
   - Need to investigate `consciousness_loop` logic for `single_run_input` handling
   - Possible cause: diagnostic plugin runs automatically on startup in offline mode?

5. **Terminal usage best practice**
   - NEVER run commands in an already-active terminal that's waiting for input
   - Always start new terminal for background/long-running jobs
   - Record terminal ID and command in this file for tracking

### Next steps:
- ✅ FIXED: Investigated why `single_run_input` was ignored
- ✅ FIXED: Issue was in `consciousness_loop` - when `single_run_input` was set, code still tried to call interface plugins
- ✅ SOLUTION: Modified `core/kernel.py` line ~254 to skip interface plugins completely in single-run mode
- ✅ VERIFIED: Headless test now works! File created at `sandbox/sandbox/headless_test.txt` with content "HEADLESS_TEST_OK"
- ⚠️ NOTE: `tool_file_system` adds `sandbox/` prefix to paths, so "sandbox/headless_test.txt" becomes "sandbox/sandbox/headless_test.txt"

### Final fix summary (2025-11-06):
**Problem:** `single_run_input` was being overridden by empty interface plugin list
**Root cause:** Code called `for plugin in interface_plugins` (empty list when disabled), then fell through to `else` branch which set `context.user_input = None`
**Fix:** Skip interface plugin section entirely when `single_run_input` is provided
**Result:** ✅ Headless mode now works correctly!

---

## 2025-11-06: Applying headless fixes to 24/7 worker

### Changes made to enable headless 24/7 worker:

1. **Modified `scripts/autonomous_main.py`:**
   - Added `os.environ['SOPHIA_DISABLE_INTERACTIVE_PLUGINS'] = '1'` BEFORE imports
   - This ensures worker runs in headless mode without blocking on interactive plugins
   - Placement is critical: must be before `from core.kernel import Kernel`

2. **Verified `core/kernel_worker.py`:**
   - ✅ Already uses `consciousness_loop(single_run_input=instruction)`
   - ✅ Has 300s timeout for task execution
   - ✅ Properly marks tasks as done/failed in queue
   - No changes needed - already using the correct approach!

3. **Complete 24/7 workflow now ready:**
   ```
   enqueue_file_write_test.py  →  autonomous_main.py  →  KernelWorker  →  consciousness_loop  →  Plan execution
   (add task to queue)            (headless worker)       (dequeue)         (execute)           (write file)
   ```

### Key lessons applied:
- Environment variables set before Kernel import
- Worker uses full consciousness_loop (not just process_single_input)
- Interactive plugins disabled to prevent blocking
- Same pattern as successful headless test

**Status:** ✅ Ready for real-world 24/7 testing
**Next step:** User will manually run `enqueue_file_write_test.py` to test full chain

---

## 2025-11-06: Worker debugging - blocking issues

### Issue 1: Interface plugins not filtered
- **Problem:** `SOPHIA_DISABLE_INTERACTIVE_PLUGINS='1'` didn't work
- **Cause:** Kernel checked for `"true"` but script set `"1"`
- **Fix:** Changed check to accept `("true", "1", "yes")` in `core/kernel.py`

### Issue 2: core_self_diagnostic hangs worker
- **Problem:** Worker hung during initialization at `core_self_diagnostic` file write
- **Cause:** Plugin calls `await fs.write_file()` but `write_file` is synchronous (not async)
- **Fix:** Added `core_self_diagnostic` to disabled plugins list in headless mode

### Issue 3: Worker calls Gemini API instead of local LLM
- **Problem:** Worker made cloud API calls despite offline mode intent
- **Root cause:** `autonomous_main.py` set `offline_mode=force_local` which defaulted to `False`
- **Fix:** Changed to `offline_mode=True` (hardcoded for MVP worker)
- **Result:** Worker now ONLY uses local Ollama LLM

### Critical fixes applied:
1. `core/kernel.py` - Skip `core_self_diagnostic` AND interface plugins in headless mode
2. `scripts/autonomous_main.py` - Force `offline_mode=True` for worker (no cloud calls)
3. Environment variable check accepts `"1"`, `"true"`, `"yes"`

**Status:** 🔄 Testing final configuration...
