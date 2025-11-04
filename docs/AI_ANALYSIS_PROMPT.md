# 🤖 PROMPT FOR AI MODEL ANALYSIS - SOPHIA PROJECT

**Purpose:** Use this prompt to get independent analysis from different LLM models (GPT-4, Claude, Gemini, etc.)

**Instructions:** Copy the prompt below into a NEW chat with different AI models. Each model will analyze the project and create a comprehensive report.

---

## 📋 COPY THIS PROMPT BELOW:

```
You are an expert AI software architect and system analyst. I need you to perform a comprehensive, unbiased analysis of the Sophia AI project.

# PROJECT CONTEXT

Sophia is an autonomous AI agent built on a Core-Plugin architecture, designed to achieve true autonomous operation with minimal human supervision. The project is at 70-85% completion toward full autonomy.

# YOUR MISSION

1. **Read and understand the entire project structure**
2. **Identify critical issues** blocking production use
3. **Assess architectural decisions** (what's good, what's problematic)
4. **Prioritize fixes** based on impact and effort
5. **Recommend next steps** for Phase 4 implementation
6. **Create a detailed markdown report** named `analysis-{your-model-name}.md`

# REQUIRED READING (in order)

## Core Documentation:
1. `/workspaces/sophia/docs/en/AGENTS.md` - Operating guidelines for AI agents
2. `/workspaces/sophia/README.md` - Project overview and vision
3. `/workspaces/sophia/docs/roberts-notes.txt` - Creator's priorities and ideas
4. `/workspaces/sophia/WORKLOG.md` - Mission history (Phases 1-3 completed)
5. `/workspaces/sophia/docs/en/roadmap/04_AUTONOMOUS_OPERATIONS.md` - Current roadmap status

## Key Project Files:
6. `/workspaces/sophia/core/kernel.py` - Main consciousness loop
7. `/workspaces/sophia/plugins/` - Browse ALL plugin files (36 total)
8. `/workspaces/sophia/run.py` - Entry point
9. `/workspaces/sophia/config/` - Configuration files

## Recent Status:
10. `/workspaces/sophia/docs/STATUS_REPORT_2025-11-04.md` - Current state analysis
11. Run: `pytest tests/ -v --tb=short 2>&1 | tail -100` to see test results
12. Run: `timeout 15 python run.py "test message" 2>&1 | head -100` to test if Sophie responds

# ANALYSIS REQUIREMENTS

## 1. SYSTEM HEALTH ASSESSMENT

Analyze and rate (1-10):
- **Architecture Quality**: Core-Plugin design, separation of concerns
- **Code Quality**: Type hints, docstrings, error handling
- **Test Coverage**: Unit tests, E2E tests, test quality
- **Documentation**: Completeness, accuracy, maintainability
- **Production Readiness**: Can it run 24/7 reliably?

## 2. CRITICAL ISSUES IDENTIFICATION

For each issue found:
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Impact**: What breaks if not fixed?
- **Root Cause**: Why did this happen?
- **Estimated Fix Time**: Hours/days
- **Dependencies**: What else needs fixing first?

## 3. ARCHITECTURAL REVIEW

Evaluate:
- **Event-Driven Loop** (Phase 1) - Is it correctly implemented?
- **Background Processes** (Phase 2) - Does async work properly?
- **Memory Consolidation** (Phase 3) - Will "dreaming" work?
- **Jules Integration** - API vs CLI approach, quota management
- **Plugin System** - Are there design flaws? Improvements needed?

## 4. TEST FAILURE ANALYSIS

Current failures (as of Nov 4, 2025):
- 12 failed tests
- 2 errors
- 179 passing

For EACH failing test:
- What's the root cause?
- Is it a real bug or test issue?
- How to fix it?
- Estimated effort?

## 5. PRIORITIZED ACTION PLAN

Create a **3-tier priority system**:

### Tier 1: BLOCKERS (must fix before anything else)
- List with estimated hours
- Dependencies between fixes
- Order of execution

### Tier 2: HIGH PRIORITY (needed for Phase 4)
- Features required for autonomous operation
- Infrastructure improvements
- Performance optimizations

### Tier 3: NICE TO HAVE (future iterations)
- UI polish
- Additional features
- Documentation improvements

## 6. PHASE 4 IMPLEMENTATION STRATEGY

Based on your analysis, propose:
- **What to build first** (roberts-notes.txt monitoring? Cost tracking? Something else?)
- **Architecture changes needed** (if any)
- **New plugins required** (specs and designs)
- **Timeline estimate** (realistic, not optimistic)
- **Risk assessment** (what could go wrong?)

## 7. CONTROVERSIAL OPINIONS WELCOME

If you think:
- The architecture has fundamental flaws → SAY SO
- The roadmap is wrong → PROPOSE BETTER
- Some code should be rewritten → EXPLAIN WHY
- Project is going in wrong direction → BE HONEST

**We want TRUTH, not politeness.**

# OUTPUT FORMAT

Create a markdown file: `analysis-{model-name}.md` with this structure:

```markdown
# 🔍 SOPHIA PROJECT ANALYSIS
**Analyst:** {Your Model Name} (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Pro)
**Date:** November 4, 2025
**Analysis Duration:** {How long you spent}

---

## 📊 EXECUTIVE SUMMARY

(3-5 sentences: Overall assessment, biggest concern, confidence in project success)

---

## ⭐ RATINGS

| Aspect | Score (1-10) | Justification |
|--------|--------------|---------------|
| Architecture Quality | X/10 | ... |
| Code Quality | X/10 | ... |
| Test Coverage | X/10 | ... |
| Documentation | X/10 | ... |
| Production Readiness | X/10 | ... |
| **Overall Health** | **X/10** | ... |

---

## 🚨 CRITICAL ISSUES

### Issue 1: {Title}
- **Severity:** CRITICAL/HIGH/MEDIUM/LOW
- **Impact:** ...
- **Root Cause:** ...
- **Fix Effort:** X hours
- **Fix Strategy:** ...

(Repeat for all critical issues)

---

## 🏗️ ARCHITECTURAL REVIEW

### Phase 1: Event-Driven Loop
- **Status:** ✅/⚠️/❌
- **Assessment:** ...
- **Concerns:** ...

### Phase 2: Background Processes
- **Status:** ✅/⚠️/❌
- **Assessment:** ...
- **Concerns:** ...

### Phase 3: Memory Consolidation
- **Status:** ✅/⚠️/❌
- **Assessment:** ...
- **Concerns:** ...

### Jules Integration
- **Assessment:** ...
- **API vs CLI:** Which approach is better?
- **Concerns:** ...

### Plugin System
- **Design Quality:** ...
- **Identified Flaws:** ...
- **Improvement Opportunities:** ...

---

## 🧪 TEST FAILURE DEEP DIVE

### Failure Category 1: {e.g., Jules CLI Tests}
- **Tests Affected:** 10 tests
- **Root Cause:** ...
- **Fix Strategy:** ...
- **Estimated Effort:** X hours

(Repeat for all failure categories)

---

## 📋 PRIORITIZED ACTION PLAN

### 🔴 TIER 1: BLOCKERS (Must Fix Now)
1. **{Task}** - {X hours} - {Why critical}
2. ...

**Total Tier 1 Effort:** X hours
**Dependencies:** {Map dependencies}

### 🟡 TIER 2: HIGH PRIORITY (Needed for Phase 4)
1. **{Task}** - {X hours} - {Why important}
2. ...

**Total Tier 2 Effort:** X hours

### 🟢 TIER 3: NICE TO HAVE (Future)
1. **{Task}** - {X hours} - {Why beneficial}
2. ...

---

## 🚀 PHASE 4 IMPLEMENTATION RECOMMENDATION

### What to Build First:
1. **{Feature}**
   - **Why:** ...
   - **Effort:** X hours
   - **Dependencies:** ...

### Architecture Changes Needed:
- ...

### New Plugins Required:
1. **{plugin_name}**
   - **Purpose:** ...
   - **Spec:** ...

### Timeline Estimate:
- Week 1: ...
- Week 2: ...
- Week 3: ...

### Risk Assessment:
- **Risk 1:** ... (Mitigation: ...)
- **Risk 2:** ... (Mitigation: ...)

---

## 💡 CONTROVERSIAL OPINIONS

(Be brutally honest here. If you think something is wrong, say it clearly.)

### Opinion 1: {Title}
**Why this matters:** ...
**My recommendation:** ...
**Counter-argument:** ...
**Final verdict:** ...

---

## 🎯 SUCCESS PROBABILITY

**Probability of achieving full autonomy:** X%

**Confidence factors:**
- ✅ {What's working in project's favor}
- ⚠️ {What's concerning}
- ❌ {What could kill the project}

**Recommended next conversation:**
- Focus on: ...
- Ask Robert about: ...
- Verify assumption: ...

---

## 📝 ADDITIONAL NOTES

(Any other observations, concerns, or recommendations)

---

**End of Analysis**
```

# VERIFICATION CHECKLIST

Before submitting your analysis, verify:
- [ ] Read ALL required documentation
- [ ] Ran test suite to see actual failures
- [ ] Tested Sophie's response to input
- [ ] Reviewed at least 10 plugin files
- [ ] Analyzed core/kernel.py thoroughly
- [ ] Provided concrete fix strategies (not vague advice)
- [ ] Estimated effort for all recommendations
- [ ] Prioritized fixes by impact/effort ratio
- [ ] Was honest about problems (didn't sugarcoat)
- [ ] Created actionable next steps

# START YOUR ANALYSIS NOW

Use all available tools:
- `read_file` - Read code and documentation
- `grep_search` - Search for patterns
- `file_search` - Find files
- `semantic_search` - Find relevant code
- `run_in_terminal` - Run tests, check behavior

**BE THOROUGH. BE HONEST. BE ACTIONABLE.**

The future of this project depends on your analysis quality.
```

---

## 📋 USAGE INSTRUCTIONS FOR ROBERT

### Step 1: Copy Prompt
Copy everything between the ``` markers above.

### Step 2: Test Multiple Models
Open new chats with different models:
- **GPT-4o** (OpenAI)
- **Claude 3.5 Sonnet** (Anthropic)
- **Gemini 2.0 Pro** (Google)
- **DeepSeek** (if available)
- **Any other top-tier model**

### Step 3: Paste and Wait
Paste the prompt and let each model complete its analysis (may take 10-30 minutes per model).

### Step 4: Collect Results
Each model will create a file like:
- `analysis-gpt4o.md`
- `analysis-claude35.md`
- `analysis-gemini2pro.md`

### Step 5: Compare and Decide
Read all analyses, look for:
- **Consensus** - What do ALL models agree on? (likely true)
- **Conflicts** - Where do models disagree? (need human judgment)
- **Unique insights** - What did only one model catch? (could be brilliant or wrong)

### Step 6: Create Final Plan
Based on the analysis, create:
- `docs/FINAL_STABILIZATION_PLAN.md` - Combines best insights from all models
- Start implementation with confidence

---

## 🎯 EXPECTED OUTCOMES

After running 3-5 different models, you should have:
- **Clear consensus** on critical blockers
- **Multiple perspectives** on architecture
- **Concrete action plans** to compare
- **Risk assessments** from different viewpoints
- **Confidence** in next steps

---

## ⚠️ IMPORTANT NOTES

1. **Each model sees SAME context** - fair comparison
2. **Models may disagree** - that's GOOD (diverse perspectives)
3. **Look for patterns** - if 4/5 models say same thing → probably right
4. **Trust your judgment** - you know the project best
5. **Use insights, not gospel** - AI analysis is input, not law

---

**Good luck with the analysis! May the best insights win! 🚀**
