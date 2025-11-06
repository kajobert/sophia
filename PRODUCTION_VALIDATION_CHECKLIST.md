# SOPHIA AMI 1.0 - Production Validation Checklist

**Date:** 2025-11-06  
**Agent:** GitHub Copilot (Agentic Mode)  
**Mission:** Final validation before AMI 1.0 → 100% Complete  
**Prerequisites:** Documentation updates complete ✅

---

## 🎯 VALIDATION OBJECTIVES

**Goal:** Validate SOPHIA AMI 1.0 in production/staging environment with real autonomous upgrade cycle

**Success Criteria:**
- ✅ At least 1 successful autonomous upgrade in production
- ✅ Validation workflow completes without manual intervention
- ✅ Rollback tested and working (simulate failure scenario)
- ✅ All edge cases handled gracefully
- ✅ No security issues identified
- ✅ Performance meets expectations

**Estimated Time:** 1-2 hours

---

## 📋 PRE-VALIDATION SETUP

### 1. Environment Preparation

- [ ] **Deploy to staging/production environment**
  - [ ] Clone repository to production server
  - [ ] Install dependencies (`uv pip sync requirements.in`)
  - [ ] Configure `.env` with production API keys
  - [ ] Verify Ollama is running (`ollama list`)
  - [ ] Test local LLM connectivity

- [ ] **Guardian (Phoenix Protocol) Setup**
  - [ ] Install systemd service (`sophia-guardian.service`)
  - [ ] Verify Guardian starts on boot
  - [ ] Test manual Guardian restart: `sudo systemctl restart sophia-guardian`
  - [ ] Check Guardian logs: `journalctl -u sophia-guardian -f`

- [ ] **Database Initialization**
  - [ ] Create `.data/` directory
  - [ ] Initialize SQLite databases (memory.db, tasks.db)
  - [ ] Verify ChromaDB directory (`.data/chroma/`)
  - [ ] Test database write permissions

- [ ] **Backup Strategy**
  - [ ] Configure backup directory (`sandbox/backups/`)
  - [ ] Verify disk space (minimum 5GB free)
  - [ ] Test backup creation: `cp test.py test.py.backup`
  - [ ] Test backup restoration

---

## 🧪 CORE FUNCTIONALITY TESTS

### 2. Basic Autonomous Operation

- [ ] **Heartbeat Verification**
  - [ ] Start SOPHIA: `python run.py`
  - [ ] Monitor logs for `💓 PROACTIVE_HEARTBEAT` every 60s
  - [ ] Verify event_bus is operational
  - [ ] Check no errors in `logs/event_loop.log`

- [ ] **Notes Reader Test**
  - [ ] Add test task to `roberts-notes.txt`:
    ```
    **Priority: 90 - Testing**
    Create a simple test file at sandbox/production_test.txt with content "PRODUCTION_OK"
    ```
  - [ ] Wait for heartbeat (max 60s)
  - [ ] Verify task appears in dashboard (http://localhost:8000/dashboard)
  - [ ] Verify file created: `cat sandbox/production_test.txt`
  - [ ] Expected: "PRODUCTION_OK"

- [ ] **Memory Consolidation Test**
  - [ ] Trigger DREAM_TRIGGER event (manual or wait for scheduler)
  - [ ] Monitor `logs/cognitive_memory_consolidator.log`
  - [ ] Verify operations moved to ChromaDB
  - [ ] Check SQLite cleanup (old entries deleted)
  - [ ] Verify DREAM_COMPLETE event published

---

## 🚀 AUTONOMOUS UPGRADE CYCLE TESTS

### 3. Successful Upgrade Scenario

**Objective:** Validate complete autonomous upgrade workflow

- [ ] **Trigger Hypothesis Creation**
  - [ ] Create intentional failure (e.g., modify plugin to fail)
  - [ ] Wait for DREAM_COMPLETE event
  - [ ] Verify hypothesis created in database:
    ```bash
    sqlite3 .data/memory.db "SELECT * FROM hypotheses ORDER BY created_at DESC LIMIT 1"
    ```
  - [ ] Check hypothesis status: `pending`

- [ ] **Approve Hypothesis for Testing**
  - [ ] Manually approve hypothesis (simulate self-tuning approval):
    ```bash
    sqlite3 .data/memory.db "UPDATE hypotheses SET status='approved' WHERE id=<HYPOTHESIS_ID>"
    ```
  - [ ] Wait for self-tuning plugin to process

- [ ] **Monitor Deployment**
  - [ ] Check `logs/cognitive_self_tuning.log` for deployment
  - [ ] Verify git commit created: `git log --oneline -1`
  - [ ] Expected: `[AUTO] Self-tuning: <description>`
  - [ ] Verify backup created: `ls sandbox/backups/`
  - [ ] Expected: `<filename>.backup.<timestamp>`

- [ ] **Verify Restart Request**
  - [ ] Check `.data/restart_request.json` exists
  - [ ] Verify `.data/upgrade_state.json` exists
  - [ ] Content should include:
    ```json
    {
      "hypothesis_id": <ID>,
      "target_file": "<path>",
      "backup_file": "<path>.backup.<timestamp>",
      "validation_attempts": 0,
      "max_attempts": 3
    }
    ```

- [ ] **Guardian Restart Coordination**
  - [ ] Guardian should detect `restart_request.json`
  - [ ] SOPHIA should restart automatically (within 5 seconds)
  - [ ] Monitor Guardian logs: `journalctl -u sophia-guardian -f`
  - [ ] Expected: "Restart request detected, restarting SOPHIA..."

- [ ] **Validation Suite Execution**
  - [ ] After restart, check `logs/kernel.log` for validation
  - [ ] Expected log: "Pending upgrade detected, running validation..."
  - [ ] Verify plugin initialization check
  - [ ] Verify test suite execution (pytest)
  - [ ] Verify regression check (error rate comparison)

- [ ] **Finalization**
  - [ ] Hypothesis status should update to `deployed_validated`
  - [ ] Verify in database:
    ```bash
    sqlite3 .data/memory.db "SELECT status FROM hypotheses WHERE id=<ID>"
    ```
  - [ ] Expected: `deployed_validated`
  - [ ] Verify upgrade state cleaned up:
    ```bash
    ls .data/upgrade_state.json
    ```
  - [ ] Expected: File not found (deleted after success)

- [ ] **PR Creation Verification**
  - [ ] Check GitHub repository for new PR
  - [ ] Verify PR title matches hypothesis description
  - [ ] Verify PR body contains:
    - Hypothesis ID and details
    - Testing results
    - Benchmark data
    - Deployment timestamp
  - [ ] Verify PR is marked as Draft (if configured)

**Success:** ✅ Complete autonomous upgrade without human intervention

---

### 4. Rollback Scenario (Failure Handling)

**Objective:** Validate automatic rollback on validation failure

- [ ] **Simulate Validation Failure**
  - [ ] Create hypothesis with intentionally broken code
  - [ ] OR modify test to fail
  - [ ] OR inject error into validation logic

- [ ] **Trigger Upgrade (same as #3)**
  - [ ] Deploy → Restart → Validation

- [ ] **Monitor Rollback**
  - [ ] Validation should fail
  - [ ] Check logs for "Validation failed" message
  - [ ] Verify backup restoration:
    ```bash
    diff <original_backup> <current_file>
    ```
  - [ ] Expected: Files are identical (backup restored)

- [ ] **Git Revert Commit**
  - [ ] Verify git commit created: `git log --oneline -1`
  - [ ] Expected: `[AUTO-ROLLBACK] Validation failed: <reason>`
  - [ ] Verify code reverted to original state

- [ ] **Hypothesis Status Update**
  - [ ] Check hypothesis status in database
  - [ ] Expected: `deployed_rollback`
  - [ ] Verify test_results field contains failure logs

- [ ] **Restart After Rollback**
  - [ ] Verify `restart_request.json` created (for rollback restart)
  - [ ] Guardian should restart SOPHIA again
  - [ ] After restart, verify original code is running
  - [ ] Expected: No validation errors

**Success:** ✅ Automatic rollback restored system to working state

---

### 5. Max Attempts Limit Test

**Objective:** Prevent infinite restart loops

- [ ] **Trigger Multiple Failures**
  - [ ] Create hypothesis that fails validation
  - [ ] Let system attempt validation 3 times
  - [ ] Each attempt increments `validation_attempts` in upgrade_state.json

- [ ] **Verify Max Attempts Enforcement**
  - [ ] After 3rd failure, check logs
  - [ ] Expected: "Max validation attempts (3) exceeded, triggering rollback"
  - [ ] Verify rollback executed
  - [ ] Verify upgrade_state.json deleted

- [ ] **Hypothesis Status**
  - [ ] Expected: `deployed_rollback`
  - [ ] Verify test_results contains "max attempts exceeded" note

**Success:** ✅ System stops trying after 3 attempts, doesn't loop forever

---

## 🔒 SECURITY VALIDATION

### 6. Security Audit

- [ ] **File Permissions**
  - [ ] Check backup file permissions:
    ```bash
    ls -la sandbox/backups/*.backup.*
    ```
  - [ ] Expected: Read/write for owner only (`-rw-------`)
  - [ ] Verify no world-readable sensitive files

- [ ] **API Key Handling**
  - [ ] Search logs for exposed API keys:
    ```bash
    grep -r "sk-" logs/ || echo "No API keys found"
    ```
  - [ ] Expected: No matches (API keys not logged)
  - [ ] Verify `.env` is in `.gitignore`

- [ ] **Git Commit Safety**
  - [ ] Check auto-generated commits for sensitive data:
    ```bash
    git log -p -1 --grep="\[AUTO\]"
    ```
  - [ ] Verify no API keys, passwords, or secrets in diffs

- [ ] **Backup Cleanup Policy**
  - [ ] Check backup retention:
    ```bash
    ls -lh sandbox/backups/ | wc -l
    ```
  - [ ] Verify old backups are cleaned up (>30 days)
  - [ ] Test manual cleanup if needed

- [ ] **Database Access**
  - [ ] Verify SQLite files have correct permissions:
    ```bash
    ls -la .data/*.db
    ```
  - [ ] Expected: `-rw-r--r--` or more restrictive

**Security Status:** ✅ No vulnerabilities identified

---

## ⚡ PERFORMANCE VALIDATION

### 7. Performance Benchmarks

- [ ] **Upgrade Cycle Performance**
  - [ ] Measure time from deployment to validation complete
  - [ ] Target: < 5 minutes for simple plugin change
  - [ ] Record actual time: _______ minutes

- [ ] **Validation Suite Speed**
  - [ ] Run test suite manually:
    ```bash
    PYTHONPATH=. .venv/bin/python -m pytest -q
    ```
  - [ ] Target: < 2 minutes for full suite
  - [ ] Record actual time: _______ seconds

- [ ] **Restart Coordination Time**
  - [ ] Measure time from restart_request.json creation to restart
  - [ ] Target: < 10 seconds
  - [ ] Record actual time: _______ seconds

- [ ] **Rollback Speed**
  - [ ] Measure time from validation failure to rollback complete
  - [ ] Target: < 30 seconds
  - [ ] Record actual time: _______ seconds

- [ ] **Memory Usage**
  - [ ] Monitor memory during upgrade:
    ```bash
    ps aux | grep python | grep sophia
    ```
  - [ ] Target: < 2GB RAM
  - [ ] Record actual: _______ MB

- [ ] **Disk Usage**
  - [ ] Check disk space after 10 upgrades:
    ```bash
    du -sh .data/ sandbox/backups/
    ```
  - [ ] Verify backups are cleaned up
  - [ ] No excessive growth (< 1GB for 10 upgrades)

**Performance:** ✅ Meets or exceeds targets

---

## 🚨 EDGE CASE TESTING

### 8. Edge Cases & Error Handling

- [ ] **Disk Full Scenario**
  - [ ] Simulate low disk space (< 100MB)
  - [ ] Trigger upgrade
  - [ ] Expected: Graceful error message, no crash
  - [ ] Verify error logged to `logs/cognitive_self_tuning.log`

- [ ] **Network Failure During PR Creation**
  - [ ] Disconnect network before deployment
  - [ ] Trigger upgrade
  - [ ] Expected: PR creation fails gracefully
  - [ ] Deployment still succeeds (PR is optional)
  - [ ] Error logged, but system continues

- [ ] **Guardian Not Running**
  - [ ] Stop Guardian: `sudo systemctl stop sophia-guardian`
  - [ ] Trigger upgrade with restart request
  - [ ] Expected: `restart_request.json` created
  - [ ] SOPHIA waits for restart (no crash)
  - [ ] Start Guardian: `sudo systemctl start sophia-guardian`
  - [ ] Verify restart happens automatically

- [ ] **Concurrent Upgrade Requests**
  - [ ] Trigger two hypotheses simultaneously
  - [ ] Expected: Only one upgrade processed at a time
  - [ ] Second upgrade queued or rejected
  - [ ] No race conditions, no corruption

- [ ] **Validation Test Timeout**
  - [ ] Create test that runs > 120 seconds
  - [ ] Trigger upgrade
  - [ ] Expected: Validation times out after 120s
  - [ ] Rollback triggered automatically

- [ ] **Missing Backup File**
  - [ ] Delete backup file before rollback
  - [ ] Trigger validation failure
  - [ ] Expected: Rollback detects missing backup
  - [ ] Error logged, hypothesis marked as `deployed_rollback`
  - [ ] System uses git revert as fallback

- [ ] **Corrupted upgrade_state.json**
  - [ ] Manually corrupt `.data/upgrade_state.json`
  - [ ] Restart SOPHIA
  - [ ] Expected: Startup check handles corrupted file
  - [ ] Error logged, file ignored or reset
  - [ ] SOPHIA starts successfully

- [ ] **Plugin Import Failure After Upgrade**
  - [ ] Deploy code with syntax error
  - [ ] Restart SOPHIA
  - [ ] Expected: Plugin initialization check detects failure
  - [ ] Validation fails, rollback triggered
  - [ ] System restored to working state

**Edge Cases:** ✅ All handled gracefully without crashes

---

## 📊 MONITORING & LOGGING

### 9. Observability Validation

- [ ] **Log File Health**
  - [ ] Verify all log files are created:
    ```bash
    ls -lh logs/
    ```
  - [ ] Expected files:
    - `kernel.log`
    - `event_loop.log`
    - `cognitive_self_tuning.log`
    - `cognitive_reflection.log`
    - `cognitive_memory_consolidator.log`

- [ ] **Log Rotation**
  - [ ] Check log file sizes:
    ```bash
    du -sh logs/*.log
    ```
  - [ ] Verify no log > 100MB (rotation working)

- [ ] **Database Queries**
  - [ ] Test hypothesis query:
    ```bash
    sqlite3 .data/memory.db "SELECT COUNT(*) FROM hypotheses"
    ```
  - [ ] Test operation tracking query:
    ```bash
    sqlite3 .data/memory.db "SELECT COUNT(*) FROM operation_tracking WHERE success=0"
    ```
  - [ ] Verify queries return results

- [ ] **Dashboard Monitoring**
  - [ ] Open dashboard: http://localhost:8000/dashboard
  - [ ] Verify "Self-Improvement Status" card displays:
    - Total hypotheses count
    - Success rate gauge
    - Current upgrade indicator (if active)
    - Last upgrade timestamp
  - [ ] Verify "Hypotheses Table" shows recent entries
  - [ ] Test refresh functionality (auto-updates every 30s)

- [ ] **API Endpoint Testing**
  - [ ] Test `/api/self_improvement` endpoint:
    ```bash
    curl http://localhost:8000/api/self_improvement | jq
    ```
  - [ ] Expected: JSON with hypotheses stats, upgrade stats, current/last upgrade
  - [ ] Test `/api/hypotheses` endpoint:
    ```bash
    curl http://localhost:8000/api/hypotheses?limit=10 | jq
    ```
  - [ ] Expected: Array of hypothesis objects

**Monitoring:** ✅ Complete observability of autonomous operations

---

## 📝 DOCUMENTATION VERIFICATION

### 10. Documentation Completeness

- [ ] **README.md**
  - [ ] Verify AMI status shows 97% (after doc updates)
  - [ ] Roadmap table includes all phases (3.2, 3.3, etc.)
  - [ ] Phase 3.7 section is accurate
  - [ ] Quick Start instructions work for new users

- [ ] **TROUBLESHOOTING_AUTONOMOUS_UPGRADE.md**
  - [ ] Verify all sections are complete
  - [ ] Test at least one troubleshooting procedure
  - [ ] Confirm log file paths are correct

- [ ] **AMI_TODO_ROADMAP.md**
  - [ ] Verify Phase 3.2, 3.3 marked as ✅ COMPLETE
  - [ ] Progress tracking shows 97%
  - [ ] Success metrics are accurate

- [ ] **Session Reports**
  - [ ] SESSION_9_COMPLETION_REPORT.md is comprehensive
  - [ ] HANDOFF_SESSION_9.md includes all Phase 3.7 details
  - [ ] WORKLOG.md is up to date

**Documentation:** ✅ Accurate and complete

---

## ✅ FINAL VALIDATION CHECKLIST

### 11. Go/No-Go Decision

**Review all sections above. AMI 1.0 is ready for production if:**

- ✅ At least 1 successful autonomous upgrade completed
- ✅ Rollback tested and working
- ✅ Max attempts limit enforced (no infinite loops)
- ✅ Security audit passed (no vulnerabilities)
- ✅ Performance meets targets
- ✅ All edge cases handled gracefully
- ✅ Monitoring and logging operational
- ✅ Documentation accurate and complete

**If ANY item is unchecked, resolve before production launch.**

---

## 🎉 POST-VALIDATION ACTIONS

### 12. Upon Successful Validation

- [ ] **Update Project Status**
  - [ ] Update README.md: "97%" → "100% ✅ COMPLETE"
  - [ ] Update AMI_TODO_ROADMAP.md: Production Validation → ✅
  - [ ] Create `AMI_1.0_COMPLETE_REPORT.md` (final summary)

- [ ] **Git Tag Release**
  - [ ] Create git tag: `git tag -a v1.0.0-ami -m "AMI 1.0 Complete"`
  - [ ] Push tag: `git push origin v1.0.0-ami`

- [ ] **Announcement**
  - [ ] Update project description
  - [ ] Create release notes
  - [ ] Announce AMI 1.0 completion 🎉

- [ ] **Celebrate!** 🍾
  - SOPHIA je nyní plně autonomní AGI s self-improvement!
  - Od chyby po opravu bez lidské intervence!
  - 97% → 100% COMPLETE! 🚀

---

## 📊 VALIDATION RESULTS TEMPLATE

**Date:** _______________  
**Duration:** ___________ hours  
**Tester:** _______________

**Results:**
- Successful Upgrades: _____ / _____
- Rollbacks Tested: _____ / _____
- Security Issues Found: _____
- Performance: ✅ Pass / ⚠️ Warning / ❌ Fail
- Edge Cases Handled: _____ / _____

**Overall Status:** ✅ PASS / ⚠️ PASS WITH WARNINGS / ❌ FAIL

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

---

**End of Production Validation Checklist**

**Next Step:** Execute validation and mark AMI 1.0 as 100% COMPLETE! 🎯

---

*Created: 2025-11-06 | Version: 1.0 | Status: Ready for Use*
