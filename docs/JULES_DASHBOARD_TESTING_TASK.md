# Task for Jules: E2E Dashboard Testing with Mock Server

**Priority:** HIGH  
**Type:** Frontend Testing  
**Estimated Time:** 10-15 minutes  
**Deliverable:** Test report + Screenshots + Proposed fixes

---

## 🎯 Objective

Test SOPHIA dashboard frontend functionality using Playwright E2E tests.  
**NO full Sophia kernel required** - uses mock data server!

---

## ✅ Prerequisites (Jules VM has all of these)

- ✅ Python 3.12+ (Jules VM: 3.12.11)
- ✅ pytest (Jules VM: pre-installed)
- ✅ playwright (installable via pip)
- ✅ chromium browser (installable via playwright)

---

## 📋 Step-by-Step Execution

### Step 1: Install Dependencies

```bash
cd sophia  # Repository root

# Install Python packages
pip install pytest pytest-playwright playwright fastapi uvicorn

# Install Playwright browsers (only chromium needed for testing)
playwright install chromium
```

**Expected:** No errors, chromium browser downloaded (~100MB)

---

### Step 2: Start Mock Dashboard Server

```bash
# In terminal 1: Start mock server
python scripts/dashboard_server_mock.py
```

**Expected output:**
```
============================================================
🎭 SOPHIA Dashboard Server - MOCK MODE
============================================================

📊 Dashboard: http://127.0.0.1:8000/dashboard
📡 API Endpoints:
   - /api/tasks
   - /api/hypotheses
   - /api/benchmarks
   - /api/logs
   - /api/stats

⚠️  MOCK MODE: All data is randomly generated
   - No database required
   - No Sophia kernel required
   - No Ollama required
   - Perfect for E2E frontend testing

Press Ctrl+C to stop
============================================================
```

**Verification:**
```bash
# In terminal 2: Test API endpoints
curl http://127.0.0.1:8000/api/tasks | jq
curl http://127.0.0.1:8000/api/hypotheses | jq
curl http://127.0.0.1:8000/api/benchmarks | jq
curl http://127.0.0.1:8000/api/stats | jq
```

All should return JSON with mock data.

---

### Step 3: Run Playwright Tests

```bash
# In terminal 2: Run E2E tests
pytest tests/e2e/test_dashboard.py -v --html=test_report.html --self-contained-html

# Or with visible browser (for debugging):
pytest tests/e2e/test_dashboard.py -v --headed --slowmo=500
```

**Expected:** 20+ tests execute, most should PASS

**Possible failures** (acceptable):
- Tool execution tests (mock server returns fake data)
- Real-time updates (no WebSocket in mock mode)
- Authentication tests (no auth in mock mode)

**Critical tests** (MUST pass):
- ✅ Page loads without errors
- ✅ All tabs visible and clickable
- ✅ Tables render with data
- ✅ Charts render (Chart.js)
- ✅ API endpoints return data
- ✅ No JavaScript console errors

---

### Step 4: Analyze Results

```bash
# Review test report
open test_report.html  # Or browse to file:///<path>/test_report.html

# Check screenshots of failures
ls screenshots/e2e_tests/
```

**For each FAILED test:**
1. **Screenshot:** What does UI look like?
2. **Error message:** What assertion failed?
3. **Root cause:** Missing element? Wrong data? Timing issue?
4. **Proposed fix:** What code change would fix it?

---

### Step 5: Create Test Report

Create file: `docs/DASHBOARD_E2E_TEST_REPORT.md`

```markdown
# Dashboard E2E Test Report

**Date:** <date>  
**Tester:** Jules (Google AI Agent)  
**Environment:** Jules VM (Ubuntu, Python 3.12, Playwright + chromium)  
**Server Mode:** Mock (no Sophia kernel)

---

## Summary

- **Total Tests:** <N>
- **Passed:** <N>
- **Failed:** <N>
- **Skipped:** <N>

---

## Test Results by Category

### 1. Page Load & Navigation
- ✅/❌ Dashboard loads without errors
- ✅/❌ All tabs render correctly
- ✅/❌ Tab switching works

### 2. Data Display
- ✅/❌ Tasks table loads data
- ✅/❌ Hypotheses table loads data
- ✅/❌ Benchmarks table loads data
- ✅/❌ Charts render (Chart.js)

### 3. API Endpoints
- ✅/❌ /api/tasks returns data
- ✅/❌ /api/hypotheses returns data
- ✅/❌ /api/benchmarks returns data
- ✅/❌ /api/stats returns data

### 4. Performance
- ✅/❌ Page load < 5 seconds
- ✅/❌ Tab switching < 1 second

---

## Failures Analysis

### Test: <test_name>
**Status:** ❌ FAILED  
**Error:** <error message>  
**Screenshot:** screenshots/e2e_tests/<filename>.png  
**Root Cause:** <explanation>  
**Proposed Fix:**
```python
# File: <file>
# Line: <line>

# Current code:
<current code>

# Proposed fix:
<fixed code>
```

---

## Recommendations

1. **Critical Fixes** (blocking issues):
   - Fix 1: <description>
   - Fix 2: <description>

2. **Minor Improvements** (nice-to-have):
   - Improvement 1: <description>
   - Improvement 2: <description>

3. **Known Limitations** (acceptable in mock mode):
   - Tool execution (no real plugins in mock)
   - Real-time updates (no WebSocket)

---

## Conclusion

Overall dashboard quality: ✅ GOOD / ⚠️ NEEDS WORK / ❌ BROKEN

**Next Steps:**
1. Apply critical fixes
2. Re-run tests to verify
3. Document known issues
```

---

## 📦 Deliverables

When task completes, commit these files to repository:

1. ✅ **`test_report.html`** - Pytest HTML report
2. ✅ **`screenshots/e2e_tests/*.png`** - Failure screenshots
3. ✅ **`docs/DASHBOARD_E2E_TEST_REPORT.md`** - Analysis + fixes
4. ✅ **(Optional)** Proposed fixes in separate commits

---

## 🎯 Success Criteria

- [ ] Mock server starts successfully
- [ ] All API endpoints return mock data
- [ ] At least 15/20 tests pass (75%+)
- [ ] Screenshots captured for all failures
- [ ] Test report created with root cause analysis
- [ ] Proposed fixes documented

---

## ⚠️ Important Notes

### Why Mock Server?

**Jules CANNOT run full Sophia kernel because:**
- ❌ No Ollama (local LLM) in Jules VM
- ❌ No access to Sophia's .data/ databases
- ❌ Sophia kernel requires many plugins, complex setup
- ❌ VM timeouts for long-running processes

**Mock server solves this:**
- ✅ Standalone Python script (no Sophia kernel)
- ✅ Generates random mock data
- ✅ All API endpoints work
- ✅ Perfect for **frontend testing** (UI, charts, tables)
- ✅ Fast startup (~2 seconds)

### What This Tests

**✅ DOES TEST:**
- Dashboard HTML/CSS/JavaScript
- Chart.js integration
- Table rendering
- Tab navigation
- API endpoint consumption
- Browser compatibility

**❌ DOES NOT TEST:**
- Real Sophia plugins
- Real database queries
- Real LLM calls
- Backend business logic
- WebSocket real-time updates

**Conclusion:** This tests **frontend quality**, not backend functionality.

---

## 🔧 Troubleshooting

**Problem:** Mock server won't start  
**Solution:** Check if port 8000 already in use: `lsof -i :8000`

**Problem:** Playwright can't find chromium  
**Solution:** Run `playwright install chromium` again

**Problem:** Tests timeout  
**Solution:** Increase timeout in conftest.py or run with `--timeout=60`

**Problem:** Screenshots not saving  
**Solution:** Check `screenshots/e2e_tests/` directory exists

---

**Task Status:** READY TO EXECUTE  
**Author:** GitHub Copilot  
**Date:** 2025-11-07
