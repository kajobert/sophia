# Troubleshooting Guide: Autonomous Self-Upgrade System

**Phase 3.7 - Autonomous Upgrade Cycle**

This guide helps you debug and resolve issues with SOPHIA's autonomous self-upgrade system.

---

## 🔍 Quick Diagnosis

### Is Your Upgrade Stuck?

Check these files in order:

1. **`.data/upgrade_state.json`** - Pending upgrade status
2. **`.data/restart_request.json`** - Guardian restart signal
3. **`logs/sophia_*.log`** - Recent logs
4. **`crash_report_*.txt`** - Crash logs (if any)

---

## 🚨 Common Issues & Solutions

### 1. Upgrade Stuck in "pending_validation"

**Symptoms:**
- `.data/upgrade_state.json` exists
- `validation_attempts` not incrementing
- SOPHIA keeps restarting

**Causes:**
- Startup check not running
- cognitive_self_tuning plugin not loaded
- upgrade_state.json malformed

**Solution:**
```bash
# Check upgrade state
cat .data/upgrade_state.json

# Expected output:
{
  "hypothesis_id": 123,
  "target_file": "plugins/test.py",
  "backup_file": ".backup/test.py.backup",
  "status": "pending_validation",
  "validation_attempts": 1,  # Should increment on each restart
  "max_attempts": 3
}

# If validation_attempts not incrementing:
# 1. Check if _check_pending_upgrade() is called in run.py
grep "_check_pending_upgrade" run.py

# 2. Check logs for startup errors
tail -100 logs/sophia_$(date +%Y%m%d).log | grep -i "pending upgrade"

# 3. Manually trigger validation (advanced):
python -c "
import asyncio
import json
from pathlib import Path
from core.kernel import Kernel

async def main():
    kernel = Kernel()
    await kernel.initialize()
    
    # Load upgrade state
    with open('.data/upgrade_state.json') as f:
        state = json.load(f)
    
    # Get plugin
    plugin = kernel.all_plugins_map.get('cognitive_self_tuning')
    if plugin:
        result = await plugin._validate_upgrade(state)
        print(f'Validation result: {result}')
    
asyncio.run(main())
"
```

---

### 2. Max Attempts Exceeded

**Symptoms:**
- upgrade_state.json shows `"validation_attempts": 3` or higher
- Automatic rollback triggered
- Hypothesis status: "deployed_rollback"

**Causes:**
- Validation fails repeatedly (tests, regressions, plugin init)
- Target file has persistent bug

**Solution:**
```bash
# 1. Check why validation failed
# Look for rollback logs
grep -A 20 "ROLLBACK INITIATED" logs/sophia_*.log

# 2. Check hypothesis for rollback reason
python -c "
from plugins.memory_sqlite import MemorySQLite
mem = MemorySQLite()
mem.setup({})

# Get hypothesis
hyp = mem.get_hypothesis_by_id(123)  # Replace with your ID
print('Status:', hyp['status'])
print('Test results:', hyp['test_results'])
"

# 3. If rollback correct, clean up manually:
rm .data/upgrade_state.json
rm .data/restart_request.json

# 4. Review the backup file to understand the issue
cat .backup/your_file.py.backup
```

---

### 3. Guardian Not Restarting

**Symptoms:**
- `.data/restart_request.json` created
- SOPHIA still running (no restart)

**Causes:**
- Guardian not monitoring restart_request.json
- Guardian not running
- Permissions issue

**Solution:**
```bash
# 1. Check if Guardian is running
ps aux | grep guardian.py

# If not running:
python guardian.py &

# 2. Check Guardian logs
tail -50 logs/guardian.log

# 3. Manually restart SOPHIA (Guardian bypass):
# Kill current SOPHIA
pkill -f "python run.py"

# Start SOPHIA (will detect pending upgrade)
python run.py

# 4. Check restart_request.json
cat .data/restart_request.json

# Expected:
{
  "reason": "autonomous_upgrade",
  "hypothesis_id": 123,
  "timestamp": "2025-11-06T10:30:00"
}
```

---

### 4. Validation Fails But Code Looks Correct

**Symptoms:**
- Code change looks fine
- Validation fails on "plugin initialization" or "tests"
- Manual testing works

**Causes:**
- Test file not found
- Plugin not in all_plugins map
- Async initialization issue

**Solution:**
```bash
# 1. Check which validation step failed
grep -A 10 "Upgrade validation FAILED" logs/sophia_*.log

# If "Plugin initialization failed":
# - Check if plugin added to kernel's all_plugins
# - Verify plugin's __init__.py imports

# If "Validation tests failed":
# - Find corresponding test file
ls test_*your_plugin*.py

# - Run tests manually
PYTHONPATH=. .venv/bin/pytest test_your_plugin.py -v

# If "Regression detected":
# - Check operation_tracking table for recent errors
python -c "
from plugins.memory_sqlite import MemorySQLite
mem = MemorySQLite()
mem.setup({})

import sqlite3
conn = sqlite3.connect('.data/sophia.db')
cur = conn.execute('SELECT * FROM operation_tracking ORDER BY id DESC LIMIT 10')
for row in cur:
    print(row)
"

# 2. If validation logic incorrect, temporarily disable:
# Edit cognitive_self_tuning.py, make validation return True
# (ONLY FOR DEBUGGING - remove after)
```

---

### 5. Backup File Missing

**Symptoms:**
- Rollback triggered
- Error: "Backup file not found"
- Original code lost

**Causes:**
- Backup not created during deployment
- Backup deleted prematurely
- File system issue

**Solution:**
```bash
# 1. Check if backup exists
ls -la .backup/

# 2. If backup missing, check git history
git log --oneline -10

# Find the commit before deployment
git show <commit_hash>:plugins/your_file.py > recovered_file.py

# 3. Restore from git
git checkout HEAD~1 -- plugins/your_file.py

# 4. Prevent future issues:
# Backup files are created in _deploy_fix()
# Check logs for backup creation message
grep "Backup created" logs/sophia_*.log

# 5. If backups consistently missing:
# Check filesystem permissions
ls -ld .backup/
# Should be writable by SOPHIA user
```

---

### 6. Git Revert Commit Failed

**Symptoms:**
- Rollback triggered
- Warning: "Rollback commit failed"
- No git revert commit created

**Causes:**
- Git not configured
- No git repository
- Merge conflicts
- Permissions issue

**Solution:**
```bash
# 1. Check git status
git status

# 2. Check if git is configured
git config --list | grep user

# If not configured:
git config user.name "SOPHIA Autonomous Agent"
git config user.email "sophia@autonomous.ai"

# 3. Check for uncommitted changes
git diff

# If dirty working directory:
git add .
git commit -m "Manual cleanup before rollback"

# 4. Manually create rollback commit
git add plugins/your_file.py
git commit -m "[MANUAL-ROLLBACK] Hypothesis #123 - Validation failed"

# 5. Check permissions
ls -la .git/

# Git directory should be writable
```

---

### 7. Hypothesis Status Not Updating

**Symptoms:**
- Upgrade completes/fails
- Hypothesis status still "deployed_awaiting_validation"
- Database not updated

**Causes:**
- Database connection issue
- SQLite lock
- update_hypothesis_status() not called

**Solution:**
```bash
# 1. Check database file
ls -la .data/sophia.db

# 2. Check for SQLite locks
lsof .data/sophia.db

# If locked, kill the process:
kill -9 <PID>

# 3. Manually update hypothesis
python -c "
from plugins.memory_sqlite import MemorySQLite
mem = MemorySQLite()
mem.setup({})

# Update status
mem.update_hypothesis_status(
    hypothesis_id=123,
    status='deployed_validated',  # or 'deployed_rollback'
    test_results={'manual_fix': True}
)

print('Status updated')
"

# 4. Check update_hypothesis_status calls in logs
grep "update_hypothesis_status" logs/sophia_*.log

# 5. Verify database schema
python -c "
import sqlite3
conn = sqlite3.connect('.data/sophia.db')
cur = conn.execute('PRAGMA table_info(hypotheses)')
for row in cur:
    print(row)
"
```

---

## 🧪 Testing & Debugging

### Manual Upgrade Test

Test upgrade workflow without waiting for real errors:

```bash
# 1. Create test plugin with intentional bug
cat > plugins/test_manual_upgrade.py << 'EOF'
from plugins.base_plugin import BasePlugin, PluginType

class TestManualUpgrade(BasePlugin):
    @property
    def name(self) -> str:
        return "test_manual_upgrade"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        pass
    
    def execute(self, context):
        # BUG: undefined variable
        return {"result": undefined_var}
EOF

# 2. Create hypothesis manually
python -c "
from plugins.memory_sqlite import MemorySQLite
from datetime import datetime
mem = MemorySQLite()
mem.setup({})

hyp_id = mem.create_hypothesis(
    hypothesis_text='Fix undefined variable bug',
    source_failure_id=None,
    priority=1,
    category='bug_fix',
    root_cause='NameError: undefined_var not defined',
    proposed_fix='Define undefined_var = 42',
    estimated_improvement='100% crash reduction'
)

print(f'Hypothesis #{hyp_id} created')
"

# 3. Apply fix
cat > plugins/test_manual_upgrade.py << 'EOF'
from plugins.base_plugin import BasePlugin, PluginType

class TestManualUpgrade(BasePlugin):
    @property
    def name(self) -> str:
        return "test_manual_upgrade"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        pass
    
    def execute(self, context):
        # FIXED: define variable
        undefined_var = 42
        return {"result": undefined_var}
EOF

# 4. Trigger upgrade manually
python -c "
import asyncio
from pathlib import Path
from plugins.cognitive_self_tuning import CognitiveSelfTuning
from unittest.mock import Mock

async def main():
    plugin = CognitiveSelfTuning()
    plugin.logger = Mock()
    plugin.db = Mock()
    plugin._config = {}
    
    # Create backup
    import shutil
    target = Path('plugins/test_manual_upgrade.py')
    backup = target.with_suffix('.backup')
    shutil.copy2(target, backup)
    
    # Trigger validation
    hypothesis = {'id': 999, 'category': 'bug_fix'}
    await plugin._trigger_autonomous_upgrade_validation(
        hypothesis,
        str(target),
        backup
    )
    
    print('Upgrade triggered! Check .data/upgrade_state.json')

asyncio.run(main())
"

# 5. Restart SOPHIA to trigger validation
python run.py
```

---

### Integration Test

Run full integration test suite:

```bash
# Run all integration tests
PYTHONPATH=. .venv/bin/pytest test_integration_autonomous_upgrade.py -v -s -m integration

# Run specific test
PYTHONPATH=. .venv/bin/pytest test_integration_autonomous_upgrade.py::TestAutonomousUpgradeIntegration::test_manual_upgrade_trigger -v -s

# Run with detailed logging
PYTHONPATH=. .venv/bin/pytest test_integration_autonomous_upgrade.py -v -s --log-cli-level=DEBUG
```

---

## 📊 Monitoring & Logs

### Key Log Locations

| File | Content |
|------|---------|
| `logs/sophia_YYYYMMDD.log` | Main SOPHIA logs |
| `logs/guardian.log` | Phoenix Protocol logs |
| `.data/upgrade_state.json` | Current upgrade state |
| `.data/restart_request.json` | Guardian restart signal |
| `crash_report_*.txt` | Crash reports |

### Log Patterns to Search

```bash
# Upgrade trigger
grep "Triggering autonomous upgrade validation" logs/sophia_*.log

# Validation results
grep -E "(Upgrade validation PASSED|FAILED)" logs/sophia_*.log

# Rollback events
grep "ROLLBACK" logs/sophia_*.log

# Hypothesis updates
grep "Updated hypothesis" logs/sophia_*.log

# Guardian restarts
grep "restarted" logs/guardian.log
```

---

## 🔧 Advanced Debugging

### Enable Debug Logging

```bash
# Run SOPHIA with debug logging
python run.py --debug

# This enables:
# - Verbose plugin initialization
# - API call logging
# - Detailed error traces
```

### Database Inspection

```bash
# Open database
sqlite3 .data/sophia.db

# List all hypotheses
SELECT id, status, category, created_at FROM hypotheses ORDER BY id DESC LIMIT 10;

# Check specific hypothesis
SELECT * FROM hypotheses WHERE id = 123;

# Check operation tracking
SELECT * FROM operation_tracking ORDER BY id DESC LIMIT 10;
```

### Clean Slate Reset

**⚠️  WARNING: This deletes all upgrade state! Use only as last resort.**

```bash
# 1. Stop SOPHIA and Guardian
pkill -f "python run.py"
pkill -f "python guardian.py"

# 2. Remove upgrade state files
rm .data/upgrade_state.json
rm .data/restart_request.json

# 3. Remove backup files (optional)
rm -rf .backup/

# 4. Reset hypothesis statuses (optional)
python -c "
import sqlite3
conn = sqlite3.connect('.data/sophia.db')
conn.execute('''
    UPDATE hypotheses 
    SET status = 'pending' 
    WHERE status IN ('deployed_awaiting_validation', 'deployed_rollback')
''')
conn.commit()
print('Hypotheses reset')
"

# 5. Restart
python run.py
```

---

## 📞 Getting Help

If you're still stuck after trying these solutions:

1. **Check logs** - Enable `--debug` mode
2. **Run integration tests** - Verify system functionality
3. **Review HANDOFF_SESSION_9.md** - Detailed Phase 3.7 documentation
4. **Check AMI_TODO_ROADMAP.md** - Known issues and limitations
5. **Open GitHub Issue** - Include logs and upgrade_state.json

---

## ✅ Prevention Best Practices

### Before Deployment

1. **Always run tests**
   ```bash
   PYTHONPATH=. .venv/bin/pytest test_phase_3_7_autonomous_upgrade.py -v
   ```

2. **Verify git configuration**
   ```bash
   git config --list | grep user
   ```

3. **Check Guardian is running**
   ```bash
   ps aux | grep guardian.py
   ```

4. **Ensure disk space**
   ```bash
   df -h .data/
   ```

### During Operation

1. **Monitor logs regularly**
   ```bash
   tail -f logs/sophia_$(date +%Y%m%d).log
   ```

2. **Check upgrade state**
   ```bash
   watch -n 5 "cat .data/upgrade_state.json 2>/dev/null || echo 'No pending upgrade'"
   ```

3. **Track hypothesis statuses**
   ```bash
   python -c "
   from plugins.memory_sqlite import MemorySQLite
   mem = MemorySQLite()
   mem.setup({})
   
   hyps = mem.get_pending_hypotheses()
   print(f'{len(hyps)} pending hypotheses')
   "
   ```

---

**Last Updated:** 2025-11-06  
**Phase 3.7 Complete** - Autonomous Self-Upgrade System Operational
