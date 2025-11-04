# JULES TASK: GitHub TUI Gems Discovery

**Worker:** GitHub Gems Hunter  
**Branch:** `nomad/night-discover-tui-gems`  
**Priority:** HIGH  
**Estimated Sessions:** 45 (free tier)

---

## 🎯 MISSION OBJECTIVE

Discover top GitHub repositories with innovative terminal UI solutions and extract reusable patterns for Sophia.

---

## 📋 TASK BREAKDOWN

### Phase 1: Repository Discovery (15 sessions)

**Search GitHub for projects with:**

**Criteria:**
- ⭐ Stars > 500 (proven quality)
- 🔄 Active (commit in last 30 days)
- 🐍 Python language
- 🎨 Using Rich library OR innovative TUI approach

**Search queries to use:**
```
language:python "rich" "layout" "live" stars:>500
language:python "terminal ui" "tui" stars:>500 pushed:>2024-10-01
language:python "async" "terminal" "interface" stars:>500
language:python topic:tui stars:>500
language:python topic:terminal-ui stars:>500
```

**Target: Find 10-15 candidates, select top 5**

**For each candidate, check:**
- README quality
- Code structure
- Recent activity
- Production usage (do people actually use it?)
- Relevance to our use case

### Phase 2: Deep Code Analysis (20 sessions)

**For top 5 repositories:**

1. **Clone locally:**
   ```bash
   git clone <repo-url> /tmp/tui-gems/<repo-name>
   ```

2. **Analyze architecture:**
   - How do they structure TUI code?
   - Layout patterns
   - State management
   - Async handling
   - Error handling

3. **Extract patterns:**
   - Sticky panels implementation
   - Live refresh strategy
   - Callback patterns
   - Performance optimizations
   - Testing approach

4. **Document findings:**
   - What's clever?
   - What could we reuse?
   - What should we avoid?

**Example projects to consider (if they meet criteria):**
- `Textualize/textual` - Advanced TUI framework
- `willmcgugan/rich` - Examples folder
- `tconbeer/harlequin` - SQL IDE in terminal
- `peterbrittain/asciimatics` - Alternative TUI
- `prompt-toolkit` based apps
- Any AI/LLM terminal UIs

### Phase 3: Pattern Extraction & Adaptation (10 sessions)

1. **Identify reusable patterns:**
   - Code snippets we can adapt
   - Architecture decisions
   - Best practices
   - Common pitfalls avoided

2. **Create examples:**
   - Adapt patterns for Sophia
   - Create proof-of-concept code
   - Document integration steps

3. **Prioritize integration:**
   - Quick wins (copy-paste ready)
   - Medium effort (adaptation needed)
   - Inspirational (major refactor)

---

## 📦 DELIVERABLES

Create these files in docs/research/:

### 1. `GITHUB_TUI_GEMS.md`
**Content:**
```markdown
# GitHub TUI Gems - Top 5 Projects

## Project 1: [Name] (⭐ 2.5k stars)
**URL:** https://github.com/...
**Last commit:** 2 days ago
**Use case:** Terminal dashboard for monitoring

### Why it's a gem
- Innovative sticky panel implementation
- Clean async architecture
- Great error handling

### Architecture highlights
```python
# Their Layout pattern
class Dashboard:
    def __init__(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1)
        )
```

### Key patterns to steal
1. **Sticky header pattern** - `src/ui.py:45-67`
2. **Live refresh optimization** - `src/display.py:123`
3. **Async callback handling** - `src/events.py:89`

### Relevance to Sophia
HIGH - Same use case (live terminal UI)

### Integration plan
- Copy sticky header pattern → interface_terminal_scifi.py
- Adapt refresh optimization → our Live mode
- Effort: 2 hours
```

### 2. `CODE_PATTERNS_TO_STEAL.md`
**Content:**
```markdown
# Reusable Code Patterns

## Pattern 1: Sticky Panel with Auto-Scroll
**Source:** [Project Name] - `src/panels.py:45`
**Use case:** Chat/log display that stays at bottom

```python
class ScrollingPanel:
    def __init__(self, max_lines: int = 100):
        self.content = Text()
        self.max_lines = max_lines
    
    def add_line(self, text: str):
        self.content.append(f"{text}\n")
        # Keep only last N lines
        lines = str(self.content).split("\n")
        if len(lines) > self.max_lines:
            self.content = Text("\n".join(lines[-self.max_lines:]))
    
    def render(self) -> Panel:
        return Panel(self.content, ...)
```

**Why it's clever:**
- Prevents memory bloat
- Auto-scrolling behavior
- Simple implementation

**How to use in Sophia:**
- Replace our current conversation Text()
- Add to interface_terminal_scifi.py:120
- Prevents infinite growth

**Effort:** 15 minutes
**Impact:** MEDIUM

---

## Pattern 2: Async Event Bus
...
```

### 3. `scripts/examples/` folder
**Content:**
- Standalone examples adapted for Sophia
- Each example runnable: `python examples/sticky_panel_demo.py`
- Demonstrates specific patterns

**Example files:**
```
scripts/examples/
├── sticky_panel_demo.py          # From Project 1
├── async_refresh_demo.py          # From Project 2  
├── multi_panel_layout_demo.py     # From Project 3
└── README.md                      # How to run examples
```

### 4. `INTEGRATION_PLAN.md`
**Content:**
```markdown
# Integration Plan - GitHub Gems Patterns

## Quick Wins (< 1 hour each)

### 1. Sticky Panel Pattern
**Source:** [Project] - Pattern 1
**File:** `plugins/interface_terminal_scifi.py`
**Lines:** 120-145
**Change:**
```diff
- self._conversation = Text()
+ self._conversation = ScrollingPanel(max_lines=100)
```
**Effort:** 15 min
**Risk:** LOW
**Test:** Run demo, check memory doesn't grow

### 2. Live Refresh Optimization
**Source:** [Project] - Pattern 2
...

## Medium Effort (1-4 hours)
...

## Inspirational (Future Work)
...
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] 10+ candidate repositories found
- [ ] Top 5 selected with clear criteria
- [ ] All 5 analyzed in depth
- [ ] Minimum 10 reusable patterns extracted
- [ ] Code examples created in scripts/examples/
- [ ] Integration plan with effort estimates
- [ ] All sources properly cited
- [ ] Examples are runnable

---

## 🔍 SEARCH STRATEGY

**GitHub Advanced Search:**
```
language:python stars:>500 pushed:>2024-10-01 "rich" in:readme
language:python stars:>500 topic:tui
language:python stars:>1000 "terminal" "ui" "async"
```

**Look in:**
- `awesome-python` lists (TUI section)
- `awesome-tui` repositories
- Rich library examples
- Textual showcase projects

**Quality indicators:**
- Active issues/PRs
- Good README with examples
- Clean code structure
- Tests present
- Used in production somewhere

---

## 🚫 CONSTRAINTS

- **NO modifications to master or feature branches**
- **ONLY research & documentation**
- **Work in nomad/night-discover-tui-gems branch**
- Clone external repos to `/tmp/` (not our workspace)
- Commit messages: `research: analyzed [project-name]`

---

## 💡 TIPS

1. **Quality over quantity** - 5 excellent projects > 10 mediocre
2. **Look for real production use** - battle-tested patterns
3. **Check their issues** - learn from their bugs
4. **Star dates matter** - old stars may mean abandoned
5. **Check dependencies** - avoid heavy frameworks
6. **Read tests** - often show best practices
7. **Look for performance commits** - optimization tricks

---

## 🎯 SUCCESS DEFINITION

This task is successful if:
1. We found 5 high-quality TUI projects
2. Extracted 10+ reusable patterns
3. Created working examples
4. Have clear integration plan
5. Can implement at least 3 patterns tomorrow

**Expected outcome:** Ready-to-use patterns that solve our sticky panel problem! 🎨

---

## 📊 EXAMPLE OUTPUT

**Expected commit history:**
```
research: initial repository scan - 15 candidates found
research: analyzed textual-examples - sticky panel pattern
research: analyzed harlequin - async refresh strategy
research: created sticky panel demo example
research: integration plan for top 3 patterns
docs: GITHUB_TUI_GEMS.md completed
```

**Expected file structure:**
```
docs/research/
├── GITHUB_TUI_GEMS.md (5 projects analyzed)
├── CODE_PATTERNS_TO_STEAL.md (10+ patterns)
└── INTEGRATION_PLAN.md (prioritized steps)

scripts/examples/
├── sticky_panel_demo.py
├── async_refresh_demo.py
└── README.md
```
