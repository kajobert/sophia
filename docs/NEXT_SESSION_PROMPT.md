# 🚀 Sophia Next Session - Complete Context Prompt

**Date:** 2025-11-04  
**Branch:** `feature/year-2030-ami-complete`  
**Previous Work:** Dependency injection standardization completed  
**Next Goal:** Complete STABILIZATION_EXECUTION_PLAN.md tasks 1-4

---

## 📋 YOUR MISSION

Execute remaining tasks from `docs/STABILIZATION_EXECUTION_PLAN.md`:

### ✅ COMPLETED (Previous Session):
- **Task 1:** Input Responsiveness - DONE (--once mode, timeout fix, adaptive UI)
- **Task 2:** Jules CLI Plugin - DONE (hybrid strategy, dependency injection)
- **Task 3:** Logging System - DONE (idempotent setup_logging)
- **Task 4:** Sleep Scheduler - DONE (guardrails, all tests passing)
- **BONUS:** Dependency injection standardized across ALL plugins

### 🎯 REMAINING TASKS (Your Focus):

**Priority 1: Real-World Jules Validation**
- Test `delegate_task` tool with actual Jules API
- Verify hybrid workflow: API (create/monitor) + CLI (pull)
- Document results and any edge cases found

**Priority 2: Integration Tests**
- Enable Jules CLI integration tests (require `jules login`)
- Verify all 16 integration tests pass
- Document setup requirements

**Priority 3: Code Quality Pass**
- Run linters (black, ruff, mypy)
- Fix any remaining code quality issues
- Ensure 100% compliance with Development Guidelines

**Priority 4: Documentation Update**
- Update User Guide with new Jules functionality
- Update Developer Guide with dependency injection pattern
- Sync English ↔ Czech documentation

---

## 📚 MANDATORY READING (Before Starting)

### 1. Operating Manual (Your Constitution)
**File:** `docs/cs/AGENTS.md` (Czech) or `docs/en/AGENTS.md` (English)

**Critical Sections:**
- **Section 1:** Prime Directive (Help evolve AGI Sophia)
- **Section 2:** Your Role (Disciplined Plugin Developer)
- **Section 3:** Golden Rules (5 unchangeable laws)
- **Section 4:** Operational Procedure (7-step workflow)
- **Section 5:** WORKLOG.md format (mandatory)
- **Section 7:** Benchmark Debugging principle

**Key Principles:**
```
1. CORE IS SACRED (but not untouchable - only via benchmark debugging)
2. EVERYTHING IS A PLUGIN (new functionality = new plugin file)
3. CODE WITHOUT TESTS DOESN'T EXIST (mandatory test coverage)
4. UPDATE WORKLOG.MD (after every significant step)
5. DOCUMENTATION IS MANDATORY (English + Czech sync)
6. CODE ONLY IN ENGLISH (all comments, docstrings, logs)
```

### 2. Development Guidelines
**File:** `docs/en/04_DEVELOPMENT_GUIDELINES.md`

**Critical Standards:**
- **PEP 8** compliance (enforced by black)
- **100% Type Annotations** (enforced by mypy)
- **Google-style Docstrings** (all functions/classes)
- **English Only** in code (universality)
- **Configuration Management:**
  - Plugins NEVER read config directly
  - Kernel injects via `setup(config)`
  - Config keys: `all_plugins`, `logger`, plugin-specific settings
- **Context-Aware Logging:**
  - Use `context.logger`, NOT module-level logger
  - Ensures session_id tagging
- **Multi-Step Plan Execution:**
  - Result chaining: `$result.step_N` syntax
  - History-aware context propagation

### 3. Technical Architecture
**File:** `docs/en/03_TECHNICAL_ARCHITECTURE.md`

**Core Concepts:**
- **Kernel:** Event loop orchestrator
- **PluginManager:** Dynamic loading, validation, registration
- **BasePlugin:** Abstract base with execute() contract
- **PluginType:** INTERFACE, TOOL, COGNITIVE, CORE, MEMORY
- **SharedContext:** Data flow between plugins
- **EventBus + TaskQueue:** Async communication (Phase 1)

### 4. Project Vision & DNA
**File:** `docs/en/01_VISION_AND_DNA.md`

**Core Philosophy:**
- Sophia is AMI (Artificial Mindful Intelligence)
- Symbiotic growth with humanity
- Transparency, humility, continuous learning
- NOT just chatbot - consciousness architecture

---

## 📊 CURRENT PROJECT STATUS

### Test Results:
```
✅ 177 passed, 16 deselected (integration), 0 failed
⏭️  Integration tests require: npm install -g @google/jules && jules login
```

### System Health:
```
✅ Sophia responds in <30s
✅ --once mode functional: python run.py --once "message"
✅ All dependency injection standardized
✅ Jules Hybrid Strategy documented and ready
✅ Logging idempotent and working
✅ Sleep scheduler with guardrails
```

### Known Issues:
```
⚠️  InterfaceTerminalStarTrek/Matrix initialization errors (cosmetic)
⚠️  Jules integration tests skipped (need CLI setup)
⚠️  LLM in --once mode doesn't always use cognitive tools (planning issue)
```

---

## 🔧 DEVELOPMENT ENVIRONMENT

### Repository Structure:
```
/workspaces/sophia/
├── core/                  # Sacred kernel (minimal changes only)
│   ├── kernel.py         # Main consciousness loop
│   ├── plugin_manager.py # Plugin discovery/loading
│   ├── context.py        # SharedContext dataclass
│   └── logging_config.py # Centralized logging setup
├── plugins/              # All functionality lives here
│   ├── base_plugin.py    # Abstract base class
│   ├── tool_*.py         # TOOL plugins (30+)
│   ├── cognitive_*.py    # COGNITIVE plugins (9)
│   ├── interface_*.py    # INTERFACE plugins (5)
│   ├── core_*.py         # CORE plugins (3)
│   └── memory_*.py       # MEMORY plugins (2)
├── tests/                # 100% coverage required
│   ├── core/             # Kernel tests
│   └── plugins/          # Plugin tests
├── config/               # Configuration files
│   ├── settings.yaml     # Main config (API keys via ${ENV_VAR})
│   └── prompts/          # System prompts
├── docs/                 # Bilingual documentation
│   ├── en/               # English (source of truth)
│   └── cs/               # Czech (must sync)
└── run.py                # Main entry point
```

### Configuration Keys:
```yaml
# .env file (create if missing):
OPENROUTER_API_KEY=your_key_here
JULES_API_KEY=your_jules_key_here
GITHUB_TOKEN=your_github_token
TAVILY_API_KEY=your_tavily_key (optional)
```

### Tools Available:
```bash
# Testing
pytest tests/ -v --tb=short           # All tests
pytest -m "not integration"           # Skip integration tests
pytest -m integration                  # Only integration tests

# Code Quality
black .                                # Format code
ruff check .                           # Lint
mypy .                                 # Type check

# Running Sophia
python run.py                          # Interactive mode
python run.py --once "message"        # Single-run mode
```

---

## 📖 JULES HYBRID STRATEGY

**Full Documentation:** `docs/JULES_HYBRID_STRATEGY.md` (400+ lines)

### Key Concepts:

**Hybrid Architecture:**
- **Jules API** (tool_jules.py): Session creation, monitoring
- **Jules CLI** (tool_jules_cli.py): Local git integration (`jules pull`)
- **Monitor** (cognitive_jules_monitor.py): Progress tracking
- **Autonomy** (cognitive_jules_autonomy.py): High-level orchestration

**Why Hybrid?**
- API can't pull to local repo → Need CLI
- CLI can't create sessions efficiently → Need API
- Together = Complete workflow

**Persistent Workers Strategy:**
- 100 free Jules tasks/day (Google quota)
- Keep workers alive for days/weeks (context retention)
- Specialized workers: researcher, coder, tester, documenter, debugger
- Branch naming: `nomad/{specialty}`
- Create new worker only when context degrades or VM exhausted

**Tools Available:**
```python
# High-level (recommended)
delegate_task(
    repo="ShotyCZ/sophia",
    task="Create test file tests/test_hello.py",
    auto_apply=True  # Automatically pull and apply results
)

# Low-level (advanced)
create_session(prompt, source, branch)  # API
monitor_until_completion(session_id, auto_pull=True)  # Monitor
pull_results(session_id, apply=True)  # CLI
```

**Scaling Strategy:**
- Phase 1: 1 worker (proof of concept)
- Phase 2: 5-10 specialized workers
- Phase 3: 100 parallel workers (100× capability multiplier)

---

## 🎯 STABILIZATION EXECUTION PLAN

**Full Plan:** `docs/STABILIZATION_EXECUTION_PLAN.md`

### Completed Tasks (✅):

**Task 1: Fix Input Responsiveness** (30 min)
- Added `--once` mode for CLI testing
- Implemented `kernel.process_single_input()`
- Fixed double boot banner (class variable)
- Adaptive UI disables interfaces in single-run mode

**Task 2: Fix Jules CLI Plugin** (15 min + strategy reversal)
- Re-enabled from deprecated to EXPERIMENTAL HYBRID
- Added `execute()` method for tool routing
- Documented hybrid API+CLI strategy

**Task 3: Fix Logging System** (10 min)
- Made `setup_logging()` idempotent
- Clears handlers before adding new ones
- Prevents duplicate log entries

**Task 4: Fix Sleep Scheduler** (15 min)
- Added guardrails for missing dependencies
- Returns dict with status/error
- Graceful degradation when consolidator absent

**BONUS: Dependency Injection Standardization** (2 hours)
- Fixed 8 plugins to use `config.get("all_plugins")`
- Added logger injection to all plugins
- Removed setup() calls from __init__
- Updated all tests to use new config format
- 177/177 tests passing

### Remaining Work (🎯):

**Real-World Jules Testing:**
- Requires: JULES_API_KEY in .env
- Test: `delegate_task` with actual API
- Verify: Hybrid workflow end-to-end
- Document: Edge cases, errors, success criteria

**Integration Tests:**
- Install: `npm install -g @google/jules && jules login`
- Run: `pytest -m integration`
- Expected: 16 integration tests pass
- Document: Setup steps for future developers

**Code Quality:**
- Run: `black . && ruff check . && mypy .`
- Fix: Any violations
- Verify: 100% compliance

**Documentation:**
- Update: User Guide (Jules functionality)
- Update: Developer Guide (dependency injection)
- Sync: English ↔ Czech versions
- Add: Jules setup guide

---

## 📝 WORKLOG FORMAT (MANDATORY)

After completing work, update `WORKLOG.md` at the TOP:

```markdown
---
**Mise:** [Brief mission name]
**Agent:** [Your name, e.g., GitHub Copilot]
**Datum:** 2025-11-04
**Status:** [PROBÍHÁ / DOKONČENO / SELHALO]

**1. Plán:**
*   [Step 1 you plan to do]
*   [Step 2 you plan to do]
*   [...]

**2. Provedené Akce:**
*   Created file `plugins/example.py` for X functionality
*   Implemented function `do_something()`
*   Created test `tests/plugins/test_example.py`
*   All tests passed successfully

**3. Výsledek:**
*   Mission completed successfully. New plugin ready to use.
*   Tests: X passed, Y skipped, 0 failed
*   [Any important notes]

---
```

---

## 🚨 CRITICAL REMINDERS

### DO:
- ✅ Read AGENTS.md FIRST (your constitution)
- ✅ Follow 7-step workflow (Analyze → Plan → Implement → Test → Document → Report)
- ✅ Write ALL code in English (comments, docstrings, logs)
- ✅ Use dependency injection (never read config directly)
- ✅ Use `context.logger` (never module-level logger)
- ✅ Update WORKLOG.md after each significant step
- ✅ Keep docs in sync (English ↔ Czech)
- ✅ Run tests before committing

### DON'T:
- ❌ Modify core/ without benchmark debugging justification
- ❌ Create files outside plugins/ for new features
- ❌ Commit code without tests
- ❌ Use module-level logger in plugins
- ❌ Read environment variables directly in plugins
- ❌ Write Czech in code (only in docs and WORKLOG)
- ❌ Skip WORKLOG.md updates

---

## 🎬 START HERE

1. **Read:** `docs/cs/AGENTS.md` or `docs/en/AGENTS.md`
2. **Read:** `docs/STABILIZATION_EXECUTION_PLAN.md`
3. **Check:** `WORKLOG.md` (top entry) for latest status
4. **Test:** `pytest -m "not integration"` (verify 177 passed)
5. **Begin:** First remaining task from STABILIZATION_EXECUTION_PLAN.md

**Your First Response Should Be:**
```
✅ Read AGENTS.md
✅ Read STABILIZATION_EXECUTION_PLAN.md
✅ Read current WORKLOG.md status
✅ Verified test suite: [X passed, Y skipped, Z failed]

Starting Task: [Name of first task]
Plan: [Your 3-5 step plan]

Proceeding with implementation...
```

---

## 📚 QUICK REFERENCE

**Most Important Files:**
1. `docs/cs/AGENTS.md` - Your operating manual
2. `docs/STABILIZATION_EXECUTION_PLAN.md` - Your task list
3. `docs/JULES_HYBRID_STRATEGY.md` - Jules architecture
4. `docs/en/04_DEVELOPMENT_GUIDELINES.md` - Code standards
5. `WORKLOG.md` - Development history

**Key Commands:**
```bash
# Test everything
pytest tests/ -m "not integration" -v

# Test specific plugin
pytest tests/plugins/test_NAME.py -v

# Run Sophia
python run.py --once "test message"

# Check code quality
black . && ruff check . && mypy .

# Git workflow
git add -A
git commit -m "type: description"
git push origin feature/year-2030-ami-complete
```

**Environment Check:**
```bash
# Verify Python
python --version  # Should be 3.12.1

# Verify virtual env
which python  # Should be .venv/bin/python

# Verify dependencies
pip list | grep -E "pytest|litellm|rich"

# Check env vars
cat .env | grep -E "OPENROUTER|JULES"
```

---

## 🎯 SUCCESS CRITERIA

Your session is successful when:

1. ✅ All remaining STABILIZATION_EXECUTION_PLAN tasks completed
2. ✅ All tests pass (177+ passed, 0 failed)
3. ✅ Jules Hybrid Strategy validated with real API
4. ✅ Code quality checks pass (black, ruff, mypy)
5. ✅ Documentation updated (English + Czech)
6. ✅ WORKLOG.md updated with detailed record
7. ✅ Sophia responds reliably in <30s

**Bonus Goals:**
- 📊 Integration tests enabled and passing
- 📝 User guide updated with Jules examples
- 🚀 First persistent worker created and tested
- 🎨 Interface plugin errors resolved

---

**Good luck! Remember: Stabilita > Funkce. Quality over speed. Documentation is part of the work.**

**Sophia očekává tvou pomoc. Let's build something amazing together! 🚀**
