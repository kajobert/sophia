# 🚀 QUICK START - AI ANALYSIS PROMPT

**Copy this ENTIRE message into a new chat with different AI models (GPT-4, Claude, Gemini, etc.)**

---

You are an expert AI software architect. Analyze the Sophia AI project and create a comprehensive analysis report.

## YOUR TASK

1. **Read these files** (in order):
   - `/workspaces/sophia/docs/en/AGENTS.md`
   - `/workspaces/sophia/README.md`
   - `/workspaces/sophia/docs/roberts-notes.txt`
   - `/workspaces/sophia/WORKLOG.md`
   - `/workspaces/sophia/docs/STATUS_REPORT_2025-11-04.md`
   - `/workspaces/sophia/core/kernel.py`
   - Browse `/workspaces/sophia/plugins/` folder (36 plugins)

2. **Run these commands**:
   ```bash
   cd /workspaces/sophia
   pytest tests/ -v --tb=short 2>&1 | tail -100
   timeout 15 python run.py "test" 2>&1 | head -100
   ```

3. **Analyze**:
   - Current test failures (12 failed, 2 errors, 179 passing)
   - Why Sophie doesn't respond to user input (timeout issue)
   - Architecture quality (Core-Plugin system, Phases 1-3)
   - Production readiness

4. **Create analysis file**: `analysis-{your-model-name}.md` with:

```markdown
# 🔍 SOPHIA PROJECT ANALYSIS
**Analyst:** {Model Name}
**Date:** November 4, 2025

## 📊 EXECUTIVE SUMMARY
{3-5 sentences: health, biggest issue, success probability}

## ⭐ RATINGS (1-10)
- Architecture Quality: X/10
- Code Quality: X/10
- Test Coverage: X/10
- Production Readiness: X/10
- **Overall Health: X/10**

## 🚨 CRITICAL ISSUES (Priority Order)

### Issue 1: {Title}
- **Severity:** CRITICAL/HIGH/MEDIUM/LOW
- **Impact:** {What breaks}
- **Root Cause:** {Why it happened}
- **Fix Effort:** X hours
- **Fix Strategy:** {Concrete steps}

{Repeat for all issues}

## 📋 PRIORITIZED ACTION PLAN

### 🔴 TIER 1: BLOCKERS (Must Fix Now)
1. {Task} - {X hours} - {Why}
2. ...
**Total: X hours**

### 🟡 TIER 2: HIGH PRIORITY (Phase 4)
1. {Task} - {X hours} - {Why}
2. ...
**Total: X hours**

### 🟢 TIER 3: NICE TO HAVE
1. {Task} - {X hours} - {Why}
2. ...

## 🚀 PHASE 4 RECOMMENDATION

**Build first:** {Feature name}
**Why:** {Reasoning}
**Effort:** {Timeline}
**Risks:** {What could go wrong}

## 💡 CONTROVERSIAL OPINIONS

{Be brutally honest - what's wrong? What should change?}

## 🎯 SUCCESS PROBABILITY: X%

**Confidence factors:**
- ✅ {Strengths}
- ⚠️ {Concerns}
- ❌ {Risks}
```

## REQUIREMENTS

- ✅ Be THOROUGH - read ALL documentation
- ✅ Be HONEST - don't sugarcoat problems
- ✅ Be ACTIONABLE - concrete fixes with time estimates
- ✅ Be PRIORITIZED - impact/effort ratio
- ✅ Test actual behavior (run commands above)

**START YOUR ANALYSIS NOW. The project's future depends on your insights.**

---

