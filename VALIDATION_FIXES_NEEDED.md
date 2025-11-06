# SOPHIA AMI 1.0 - Critical Fixes Needed for Production

**Date:** 2025-11-06  
**Priority:** P0 - Blocking Production Launch  
**Estimated Fix Time:** 2-4 hours

---

## 🚨 CRITICAL ISSUE #1: SOPHIA Single-Run Termination

### Problem
SOPHIA starts, processes initial tasks, then exits instead of running continuously.

### Evidence
```
{"asctime": "2025-11-06 16:53:00,940", "name": "core.event_loop", "levelname": "INFO", 
 "message": "Event-driven consciousness loop finished", "plugin_name": "EventDrivenLoop"}
{"asctime": "2025-11-06 16:53:03,902", "name": "sophia.task_queue", "levelname": "INFO", 
 "message": "Stopping TaskQueue...", "plugin_name": "TaskQueue"}
```

### Impact
- Cannot observe autonomous upgrade cycles
- Heartbeat runs once, then stops
- Blocks all integration testing

### Root Cause (Suspected)
1. Event loop terminating after single input processing
2. No "keep-alive" mechanism in event-driven loop
3. Possible issue with `single_run_input` parameter

### Fix Location
- `core/event_loop.py` - EventDrivenLoop.run()
- `run.py` - Startup configuration

### Proposed Fix
```python
# In core/event_loop.py
async def run(self, context: SharedContext, single_run_input: str | None = None):
    """Run event-driven loop continuously."""
    
    # Start background tasks
    asyncio.create_task(self._heartbeat_loop())
    asyncio.create_task(self._check_input())
    
    # NEW: If single_run_input provided, process it but DON'T exit
    if single_run_input:
        await self._process_user_input(single_run_input, context)
        # Continue running after processing
    
    # Main event loop - run forever
    try:
        while True:
            await asyncio.sleep(1)  # Keep loop alive
            # Event handlers run in background tasks
    except asyncio.CancelledError:
        logger.info("Event-driven loop cancelled")
```

### Testing
1. Start SOPHIA: `python run.py --ui classic --no-webui`
2. Wait 120 seconds
3. Verify at least 2 PROACTIVE_HEARTBEAT events in logs
4. SOPHIA should NOT terminate

---

## 🚨 CRITICAL ISSUE #2: Missing Kernel Startup Upgrade Check

### Problem
Kernel does not check for pending upgrades on startup, so validation never runs after restart.

### Evidence
```bash
# grep result: No matches found
grep "upgrade_state|pending.*validation" core/kernel.py
```

### Impact
- Autonomous upgrade cycle cannot complete
- After restart_request.json is created, nothing happens
- Core AMI 1.0 feature non-functional

### Expected Behavior
Per `PRODUCTION_VALIDATION_CHECKLIST.md`:
```
After restart, check logs/kernel.log for validation
Expected log: "Pending upgrade detected, running validation..."
```

### Fix Location
- `core/kernel.py` - `initialize()` method

### Proposed Fix
```python
# In core/kernel.py, add to initialize() method

async def initialize(self):
    """Loads prompts, discovers, and sets up all plugins."""
    
    # AMI 1.0: Check for recovery mode
    if "--recovery-from-crash" in sys.argv:
        await self._handle_recovery_mode()
    
    # NEW: Check for pending autonomous upgrade
    await self._check_pending_upgrade()
    
    # ... rest of initialization ...

async def _check_pending_upgrade(self):
    """Check for pending autonomous upgrade and trigger validation."""
    from pathlib import Path
    import json
    
    upgrade_state_file = Path(".data/upgrade_state.json")
    
    if not upgrade_state_file.exists():
        return  # No pending upgrade
    
    try:
        with open(upgrade_state_file, 'r') as f:
            upgrade_state = json.load(f)
        
        logger.warning(
            f"🔄 Pending upgrade detected (hypothesis {upgrade_state['hypothesis_id']}), "
            f"running validation...",
            extra={"plugin_name": "Kernel"}
        )
        
        # Store for later (after event_bus is initialized)
        self._pending_upgrade_state = upgrade_state
        
    except Exception as e:
        logger.error(
            f"Failed to load upgrade state: {e}",
            exc_info=True,
            extra={"plugin_name": "Kernel"}
        )
```

```python
# In consciousness_loop(), after event_bus is started:

if self.use_event_driven:
    from core.events import Event, EventType, EventPriority
    
    # ... existing SYSTEM_READY event ...
    
    # NEW: Trigger validation if pending upgrade
    if hasattr(self, '_pending_upgrade_state'):
        logger.warning(
            "🔄 Publishing UPGRADE_VALIDATION_REQUIRED event",
            extra={"plugin_name": "Kernel"}
        )
        self.event_bus.publish(
            Event(
                event_type=EventType.UPGRADE_VALIDATION_REQUIRED,
                source="kernel",
                priority=EventPriority.CRITICAL,
                data=self._pending_upgrade_state
            )
        )
```

### Additional Changes Needed

1. **Add EventType.UPGRADE_VALIDATION_REQUIRED** to `core/events.py`
2. **Subscribe in CognitiveSelfTuning** plugin to handle validation
3. **Test with mock upgrade_state.json**

### Testing
1. Create `.data/upgrade_state.json`:
   ```json
   {
     "hypothesis_id": 999,
     "target_file": "plugins/test_plugin.py",
     "backup_file": "plugins/test_plugin.backup",
     "status": "pending_validation",
     "validation_attempts": 0
   }
   ```
2. Restart SOPHIA
3. Check logs for "Pending upgrade detected, running validation..."
4. Verify validation triggered

---

## 🚨 HIGH PRIORITY ISSUE #3: EventType.SYSTEM_NOTIFICATION Missing

### Problem
Sleep scheduler tries to use non-existent `EventType.SYSTEM_NOTIFICATION`.

### Evidence
```python
File "/mnt/c/SOPHIA/sophia/plugins/core_sleep_scheduler.py", line 252
    event_type=EventType.SYSTEM_NOTIFICATION,
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: type object 'EventType' has no attribute 'SYSTEM_NOTIFICATION'
```

### Impact
- Memory consolidation completion events fail
- Crashes sleep scheduler
- Spam in logs

### Fix Location
- `plugins/core_sleep_scheduler.py:252`

### Option 1: Use Existing Event Type
```python
# Replace line 252
event_type=EventType.UI_NOTIFICATION,  # Changed from SYSTEM_NOTIFICATION
```

### Option 2: Add New Event Type
```python
# In core/events.py
class EventType(Enum):
    # ... existing types ...
    SYSTEM_NOTIFICATION = "system_notification"  # NEW
```

### Recommended: Option 1 (simpler, less invasive)

### Testing
1. Wait for consolidation trigger (or manually trigger DREAM_TRIGGER event)
2. Check logs for consolidation completion
3. Verify no AttributeError

---

## ⚠️ MEDIUM PRIORITY ISSUE #4: WebUI Not Responding

### Problem
WebUI reports "started" but port 8000 not listening.

### Evidence
```
Log: "WebUI server started at http://127.0.0.1:8000"
Test: curl http://127.0.0.1:8000/ → No response
Test: ss -tuln | grep 8000 → Port 8000 not listening
```

### Impact
- No dashboard monitoring
- Cannot use /api/self_improvement endpoint
- Degraded user experience

### Possible Causes
1. FastAPI/uvicorn not fully starting
2. Binding to wrong interface
3. Event loop termination kills WebUI server
4. `--no-webui` flag conflict

### Investigation Steps
1. Check `plugins/interface_webui.py` startup sequence
2. Verify uvicorn configuration
3. Check for exceptions in WebUI startup
4. Test without `--no-webui` flag

### Testing
1. Start SOPHIA without `--no-webui`: `python run.py --ui classic`
2. Check `ss -tuln | grep 8000`
3. Test `curl http://127.0.0.1:8000/`
4. Open browser to http://127.0.0.1:8000/dashboard

---

## 🔧 LOW PRIORITY ISSUE #5: InterfaceTerminalMatrix Plugin Error

### Problem
Plugin signature mismatch causes repeated errors.

### Evidence
```
TypeError: InterfaceTerminalMatrix.execute() takes 1 positional argument but 2 were given
```

### Impact
- Log spam
- No functional impact (interface plugin, not critical)

### Fix Location
- `plugins/interface_terminal_matrix.py`

### Fix
Update `execute()` method signature to match BasePlugin contract:
```python
async def execute(self, context: SharedContext) -> Dict[str, Any]:
    # Changed from: async def execute(self) -> Dict[str, Any]:
    # Add context parameter
```

---

## 📋 FIX CHECKLIST

### Before Re-Validation

- [ ] Fix #1: SOPHIA continuous operation mode
- [ ] Fix #2: Kernel startup upgrade check
- [ ] Fix #3: EventType.SYSTEM_NOTIFICATION
- [ ] Run unit tests: `pytest test_phase_3_7_autonomous_upgrade.py -v`
- [ ] Verify all 15 tests still pass
- [ ] Start SOPHIA and verify continuous operation (>2 minutes)
- [ ] Test pending upgrade detection (manual .json file)

### After Fixes Applied

- [ ] Re-run full validation checklist
- [ ] Create approved hypothesis
- [ ] Observe complete upgrade cycle
- [ ] Test rollback scenario
- [ ] Run edge case tests
- [ ] Update `VALIDATION_RESULTS_2025-11-06.md` with PASS status
- [ ] Create `AMI_1.0_COMPLETE_REPORT.md`
- [ ] Update `README.md` to 100%
- [ ] Git tag `v1.0.0-ami`

---

## 🎯 SUCCESS CRITERIA

AMI 1.0 is ready for production when:

✅ SOPHIA runs continuously (>10 minutes without termination)  
✅ At least 1 complete autonomous upgrade cycle observed  
✅ Rollback tested and working  
✅ All 15 unit tests pass  
✅ No critical errors in logs  
✅ WebUI responding on port 8000  
✅ Documentation updated to 100%

---

## 📞 SUPPORT

If you encounter issues during fixes:

1. Check test output: `pytest -v --tb=long`
2. Review logs: `tail -f logs/sophia.log`
3. Validate database: `sqlite3 .data/memory.db "SELECT * FROM hypotheses"`
4. Check process status: `ps aux | grep sophia`

---

**End of Fix Guide**

**Estimated Time to Production:** 2-4 hours (with focused development)  
**Complexity:** Medium (requires core architecture changes)  
**Risk:** Low (changes isolated, well-tested)

---

*Generated: 2025-11-06 22:35 UTC*  
*For: SOPHIA AMI 1.0 Production Launch*  
*Next Action: Apply fixes and re-validate*
