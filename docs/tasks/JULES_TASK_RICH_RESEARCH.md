# JULES TASK: Rich Library Best Practices Research

**Worker:** Documentation Scholar  
**Branch:** `nomad/night-research-rich-best-practices`  
**Priority:** HIGH  
**Estimated Sessions:** 50 (free tier)

---

## 🎯 MISSION OBJECTIVE

Study Rich library (Textualize/rich) production patterns and create actionable improvement recommendations for our `interface_terminal_scifi.py`.

---

## 📋 TASK BREAKDOWN

### Phase 1: Documentation Study (15 sessions)

1. **Clone and explore Rich repository:**
   ```bash
   git clone https://github.com/Textualize/rich.git /tmp/rich
   ```

2. **Read key documentation:**
   - Layout documentation
   - Live display guide
   - Panel and Text documentation
   - Performance best practices
   - Common pitfalls

3. **Focus on:**
   - How to properly accumulate Text() content
   - When to call `refresh()` vs `update()`
   - Layout update patterns
   - Callback integration with Live mode

### Phase 2: Production Examples Analysis (20 sessions)

1. **Find real-world apps using Rich:**
   - Search GitHub: `"rich live layout python" language:python stars:>100`
   - Look for: TUI apps, terminals, monitoring tools
   - Priority: Apps with sticky panels

2. **Analyze top 5 projects:**
   - How they structure Layout
   - How they handle Live refresh
   - How they accumulate conversation/logs
   - Performance optimizations

3. **Extract code patterns:**
   - Copy relevant snippets
   - Document what they do differently
   - Note any clever tricks

### Phase 3: Create Recommendations (15 sessions)

1. **Compare with our current implementation:**
   - Read `plugins/interface_terminal_scifi.py`
   - Identify gaps vs best practices
   - Find potential bugs

2. **Create improvement plan:**
   - List 3-5 concrete changes
   - Provide code examples
   - Estimate impact (high/medium/low)

3. **Write documentation:**
   - RICH_BEST_PRACTICES.md
   - RICH_PRODUCTION_EXAMPLES.md
   - SCIFI_UI_IMPROVEMENTS.md

---

## 📦 DELIVERABLES

Create these files in docs/research/:

### 1. `RICH_BEST_PRACTICES.md`
**Content:**
- Top 10 patterns from official docs
- Common mistakes to avoid
- Performance tips
- Code snippets for each pattern

**Format:**
```markdown
## Pattern 1: Text Accumulation
**What:** How to properly build up Text() objects
**Why:** Prevents memory leaks and improves performance
**How:**
```python
# Good pattern
text = Text()
text.append("new content\n")
panel.update(Panel(text))
```
**When to use:** For conversation displays, logs
**Source:** [link]
```

### 2. `RICH_PRODUCTION_EXAMPLES.md`
**Content:**
- 5 real GitHub projects analyzed
- For each: stars, use case, key patterns
- Links to specific code files
- Screenshots (ASCII art) of their UI

**Format:**
```markdown
## Project 1: [Name] (⭐ 1.2k stars)
**URL:** https://github.com/...
**Use case:** Terminal dashboard
**Key pattern:** Fixed header + scrolling content
**Code reference:** `src/ui.py:45-67`
**What we can learn:** Their refresh strategy...
```

### 3. `SCIFI_UI_IMPROVEMENTS.md`
**Content:**
- Comparison: Our current vs best practices
- 3-5 concrete improvements
- Priority (P0/P1/P2)
- Implementation steps

**Format:**
```markdown
## Improvement 1: Fix Text Accumulation Pattern
**Current problem:** Messages disappear after refresh
**Root cause:** Creating new Text() on each update
**Best practice:** Use single Text() accumulator
**Implementation:**
```python
# In __init__:
self._conversation = Text()

# In display_message:
self._conversation.append(f"{message}\n")
panel.update(Panel(self._conversation))
```
**Priority:** P0 (critical for sticky panels)
**Effort:** 10 minutes
**Impact:** HIGH
```

---

## ✅ ACCEPTANCE CRITERIA

- [ ] At least 5 production examples analyzed
- [ ] All 3 deliverable files created
- [ ] Minimum 10 best practices documented
- [ ] Concrete code examples for each recommendation
- [ ] Our interface_terminal_scifi.py analyzed
- [ ] Implementation steps for each improvement
- [ ] Links to all sources provided

---

## 🔍 SEARCH QUERIES TO USE

**GitHub:**
```
"rich live layout" language:python stars:>100
"rich terminal ui" language:python
"rich panel update" language:python
"textual tui" language:python stars:>500
```

**Documentation:**
- https://rich.readthedocs.io/en/latest/layout.html
- https://rich.readthedocs.io/en/latest/live.html
- https://rich.readthedocs.io/en/latest/panel.html

**Google/Tavily:**
```
"rich library best practices python"
"rich live display performance"
"sticky panels rich python"
```

---

## 🚫 CONSTRAINTS

- **NO modifications to master or feature branches**
- **NO changes to core code** (only research & docs)
- **ONLY work in nomad/night-research-rich-best-practices branch**
- Commit messages: `research: {topic} - {finding}`

---

## 💡 TIPS

1. Start with official docs - they're comprehensive
2. Look for apps similar to our use case (conversational UI)
3. Pay attention to `refresh()` frequency - affects performance
4. Note any `Live` context manager best practices
5. Check if they use `auto_refresh` or manual refresh
6. Look for Text() vs string usage patterns

---

## 🎯 SUCCESS DEFINITION

This task is successful if:
1. We understand why our panels don't update properly
2. We have 3-5 concrete fixes to implement tomorrow
3. All fixes have code examples
4. Documentation is clear and actionable

**Expected outcome:** Tomorrow morning we can implement fixes in 15 minutes! 🚀
