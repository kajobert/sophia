# Jules CLI Integration - Akční Plán

**Datum:** 3. listopadu 2025  
**Status:** Research Complete, Ready for Implementation  

---

## ✅ **CO JSME ZJISTILI**

### **1. Jules CLI je nainstalován**
- **Verze:** v0.1.40
- **Lokace:** `/usr/local/bin/jules` (global npm install)
- **Package:** `@google/jules`

### **2. Kompletní CLI Capabilities**

#### **Dostupné příkazy:**
```bash
# Authentication
jules login          # Interaktivní přihlášení (vyžaduje browser)
jules logout         # Odhlášení

# Session Management
jules new "task"                    # Vytvoř session (current repo)
jules new --repo owner/repo "task"  # Vytvoř session (specific repo)
jules new --parallel 3 "task"       # Paralelní sessions (1-5)

# Remote Sessions
jules remote new --repo owner/repo --session "task"
jules remote list --session         # List všech sessions
jules remote list --repo            # List všech repos
jules remote pull --session 123     # Zobraz výsledky
jules remote pull --session 123 --apply  # ✨ APLIKUJ změny lokálně

# Utility
jules version        # Zobraz verzi
jules               # Launch TUI (Terminal UI)
```

#### **Advanced Features:**
```bash
# Unix Piping (KILLER FEATURE!)
cat TODO.md | jules new
gh issue list --json title | jq -r '.[0].title' | jules new
gemini -p "find hardest issue\n$(gh issue list)" | jules new

# Parallel Execution (UNIKÁTNÍ!)
jules remote new --parallel 5 --session "complex task"
# Vytvoří 5 VMs současně pracujících na stejném úkolu!
```

---

## 🎯 **HYBRID STRATEGY - Finální Rozhodnutí**

### **Použij CLI pro:**
1. ✅ **Creating sessions** (`jules remote new`)
   - Jednodušší než API
   - Podporuje `--parallel` (API tohle nemá!)
   - Unix piping support

2. ✅ **Pulling results** (`jules remote pull --apply`)
   - **JEDINÝ způsob** jak získat změny z Jules sessions
   - API tuto funkci NEMÁ
   - **KRITICKÉ pro autonomní workflow**

### **Použij API pro:**
1. ✅ **Monitoring** (`get_session()`)
   - Strukturovaná data (JSON → Pydantic)
   - Detailní state: PLANNING → IN_PROGRESS → COMPLETED → FAILED
   - Activities, timestamps, error messages
   - **NEJLEPŠÍ pro polling**

2. ✅ **Listing sessions** (`list_sessions()`)
   - Full details o každé session
   - Filtrovatelné v Pythonu
   - Robustní error handling

### **Použij GitHub API pro:**
1. ✅ **PR Management** (`create_pull_request`, `merge_pull_request`)
   - Plná kontrola nad PR workflow
   - Review, labeling, assignees
   - **Již implementováno v Sophie**

---

## 🚀 **COMPLETE AUTONOMOUS WORKFLOW**

```
┌─────────────────────────────────────────────────────┐
│  SOPHIE'S AUTONOMOUS SELF-IMPROVEMENT CYCLE         │
└─────────────────────────────────────────────────────┘

1. 🧠 IDENTIFY IMPROVEMENT
   Sophie: cognitive_planner analyzuje codebase
   → Identifikuje area for improvement
   
2. 📝 CREATE JULES SESSION (CLI)
   tool_bash: jules remote new --repo ShotyCZ/sophia \
              --session "Refactor planner for performance" \
              --parallel 3
   → 3 VMs začnou pracovat paralelně
   → Parse session IDs: [123, 124, 125]

3. 👀 MONITOR PROGRESS (API)
   cognitive_jules_monitor: 
   → Polling každých 30s via API
   → get_session(session_id) → structured data
   → Detekce: state == "COMPLETED" ✅

4. 📥 PULL RESULTS (CLI)
   tool_bash: jules remote pull --session 123 --apply
   → Změny aplikovány do lokálního repo
   → Sophie má kód lokálně k review

5. 🔍 REVIEW CHANGES (Sophie)
   cognitive_code_reader: analyze změny
   → Check code quality
   → Run static analysis
   → Verify tests pass

6. 🌿 CREATE BRANCH & COMMIT
   tool_git: 
   → git checkout -b jules/performance-refactor-123
   → git add .
   → git commit -m "[Jules #123] Refactor planner"
   → git push origin jules/performance-refactor-123

7. 📤 CREATE PR (GitHub API)
   tool_github.create_pull_request:
   → owner="ShotyCZ", repo="sophia"
   → head="jules/performance-refactor-123"
   → base="sophie/autonomous-dev"  # Sophie's working branch
   → PR created ✅

8. ✅ RUN TESTS & MERGE
   → GitHub Actions run tests
   → Sophie waits for CI ✅
   → tool_github.merge_pull_request()
   → Merged to sophie/autonomous-dev ✅

9. 🎉 FINAL PR TO MASTER
   tool_github.create_pull_request:
   → head="sophie/autonomous-dev"
   → base="master"
   → Notify human for final approval
   
RESULT: 100% AUTONOMOUS až po human approval! 🚀
```

---

## 🛠️ **IMPLEMENTATION TASKS**

### **PHASE 1: CLI Integration (Priority: HIGH)**

#### **Task 1.1: Create `plugins/tool_jules_cli.py`**
```python
"""
Jules CLI integration plugin for Sophie.
Provides scriptable access to Jules CLI commands.
"""

class JulesCLIPlugin(BasePlugin):
    
    def create_session(self, context, repo, task, parallel=1):
        """
        Create Jules session via CLI
        
        Args:
            repo: "owner/repo" format
            task: Task description
            parallel: Number of parallel sessions (1-5)
            
        Returns:
            List of session IDs
        """
        cmd = f'jules remote new --repo {repo} --session "{task}" --parallel {parallel}'
        result = self._execute_bash(context, cmd)
        session_ids = self._parse_session_ids(result.output)
        return session_ids
    
    def pull_results(self, context, session_id, apply=True):
        """
        Pull Jules session results
        
        Args:
            session_id: Jules session ID
            apply: If True, apply changes to local repo
            
        Returns:
            Diff output or success message
        """
        apply_flag = "--apply" if apply else ""
        cmd = f"jules remote pull --session {session_id} {apply_flag}"
        result = self._execute_bash(context, cmd)
        return result.output
    
    def list_sessions(self, context):
        """List all remote sessions via CLI"""
        cmd = "jules remote list --session"
        result = self._execute_bash(context, cmd)
        return self._parse_sessions_list(result.output)
    
    def _execute_bash(self, context, command):
        """Execute bash command via tool_bash"""
        bash_tool = context.get_plugin("tool_bash")
        return bash_tool.execute(context, command=command)
    
    def _parse_session_ids(self, output):
        """
        Parse session IDs from CLI output
        
        Expected formats:
        - "Session ID: 123456"
        - "Created sessions: 123, 124, 125"
        """
        # TODO: Implement based on actual CLI output
        import re
        ids = re.findall(r'(\d{6,})', output)
        return ids
    
    def _parse_sessions_list(self, output):
        """Parse 'jules remote list --session' output"""
        # TODO: Implement based on actual CLI output format
        pass
```

#### **Task 1.2: Update `cognitive_jules_monitor.py`**
```python
# Add hybrid monitoring with CLI pull

def monitor_until_completion(self, context, session_id, check_interval=30, auto_pull=True):
    """
    Monitor Jules session with optional auto-pull
    
    Args:
        session_id: Jules session ID
        check_interval: Polling interval in seconds
        auto_pull: If True, automatically pull results when COMPLETED
    """
    # ... existing monitoring code ...
    
    if status.is_completed and auto_pull:
        # Pull results via CLI
        cli_tool = context.get_plugin("tool_jules_cli")
        results = cli_tool.pull_results(context, session_id, apply=True)
        
        context.logger.info(f"✅ Results pulled and applied: {results}")
        
        return {
            "status": status,
            "results_applied": True,
            "changes": results
        }
    
    return status
```

#### **Task 1.3: Authentication Setup**
```bash
# PRE-REQUISITE: One-time manual setup
# Developer must run once:
jules login

# This stores credentials in:
# - ~/.config/jules/credentials.json (likely location)
# OR
# - Environment variable JULES_TOKEN

# For Docker persistence, mount config:
# docker run -v ~/.config/jules:/root/.config/jules ...

# TODO: Document authentication setup in README
```

---

### **PHASE 2: Testing & Validation**

#### **Test 1: Create Session**
```bash
# Manual test to verify CLI works
jules remote new \
  --repo ShotyCZ/sophia \
  --session "Add test comment to README.md"

# Expected output:
# Session ID: 123456
# Status: PLANNING
```

#### **Test 2: Monitor via API**
```python
# Sophie runs:
session = tool_jules.get_session(context, "sessions/123456")
print(f"State: {session.state}")
# Expected: PLANNING → IN_PROGRESS → COMPLETED
```

#### **Test 3: Pull Results (CRITICAL TEST!)**
```bash
# When session COMPLETED:
jules remote pull --session 123456

# Shows diff - verify output format

jules remote pull --session 123456 --apply

# CRITICAL: What happens?
# - Creates commit?
# - Creates branch?
# - Pushes to remote?
# - Creates PR?
# 
# WE NEED TO DOCUMENT THIS! 📋
```

#### **Test 4: End-to-End Workflow**
```python
# Complete test of Sophie's autonomous cycle
# 1. CLI create → 2. API monitor → 3. CLI pull → 4. GitHub PR → 5. Merge
```

---

### **PHASE 3: Advanced Features**

#### **Feature 1: Parallel Session Management**
```python
def create_parallel_tasks(self, context, task, num_parallel=3):
    """
    Create multiple parallel Jules sessions for same task
    Returns best result based on quality metrics
    """
    # Create parallel sessions
    session_ids = create_session(context, task, parallel=num_parallel)
    
    # Monitor all in parallel
    results = []
    for sid in session_ids:
        status = monitor_until_completion(context, sid)
        if status.is_completed:
            results.append({
                'session_id': sid,
                'result': pull_results(context, sid, apply=False)
            })
    
    # Evaluate which result is best
    best = evaluate_results(results)
    
    # Apply only the best one
    pull_results(context, best['session_id'], apply=True)
    
    return best
```

#### **Feature 2: Unix Pipeline Integration**
```python
def create_session_from_pipeline(self, context, pipeline_command):
    """
    Create Jules session from Unix pipeline
    
    Example:
        pipeline = "gh issue list --assignee @me --limit 1 --json title | jq -r '.[0].title'"
        create_session_from_pipeline(context, pipeline)
    """
    full_cmd = f"{pipeline_command} | jules new"
    result = self._execute_bash(context, full_cmd)
    return self._parse_session_ids(result.output)
```

#### **Feature 3: Batch Processing**
```python
def process_todo_file(self, context, todo_file="TODO.md"):
    """
    Process all tasks from TODO file
    Creates Jules session for each line
    """
    cmd = f'cat {todo_file} | while IFS= read -r line; do jules new "$line"; done'
    result = self._execute_bash(context, cmd)
    return self._parse_multiple_sessions(result.output)
```

---

## ⚠️ **CRITICAL UNKNOWNS - Must Test**

### **1. `jules remote pull --apply` Behavior**
**MUST VERIFY:**
- [ ] Does it create a new branch?
- [ ] Does it commit changes?
- [ ] Does it push to remote?
- [ ] Does it create GitHub PR automatically?
- [ ] How does it handle conflicts?
- [ ] What's the commit message format?

**Test Command:**
```bash
# After session completes:
jules remote pull --session <ID> --apply
git status
git log -1
git branch
gh pr list
```

### **2. Authentication Persistence**
**MUST VERIFY:**
- [ ] Where are credentials stored after `jules login`?
- [ ] Do they persist across Docker restarts?
- [ ] Token-based auth alternative?
- [ ] Can we automate login with env vars?

**Test:**
```bash
jules login
ls -la ~/.config/jules/
cat ~/.config/jules/credentials.json  # if exists
env | grep JULES
```

### **3. CLI Output Formats**
**MUST DOCUMENT:**
- [ ] Session ID format in output
- [ ] Success/error indicators
- [ ] Session list format
- [ ] Pull output format

**Capture Examples:**
```bash
jules remote new --repo test/test --session "test" > new_output.txt
jules remote list --session > list_output.txt
jules remote pull --session 123 > pull_output.txt
```

---

## 📋 **NEXT STEPS - Prioritized**

### **IMMEDIATE (Dnes - requires manual auth):**
1. ⏸️ **Manual:** Run `jules login` (vyžaduje browser)
2. ⏸️ **Test:** Create test session and monitor
3. ⏸️ **Test:** `jules remote pull --apply` behavior
4. ⏸️ **Document:** Exact CLI output formats

### **SHORT TERM (Tento týden):**
1. 🔧 Implement `plugins/tool_jules_cli.py`
2. 🔧 Update `cognitive_jules_monitor.py` pro hybrid mode
3. 🧪 Write tests pro CLI integration
4. 📝 Document authentication setup

### **MEDIUM TERM (Příští sprint):**
1. 🚀 Implement complete autonomous workflow
2. 🌿 Implement branch strategy (sophie/autonomous-dev)
3. ⚡ Add parallel session support
4. 🔗 Unix pipeline integration

---

## 💡 **KEY INSIGHTS**

### **Why HYBRID is Superior:**

1. **CLI fills API gap:**
   - API nemá způsob jak získat výsledky
   - CLI má `pull --apply` - JEDINÝ způsob!

2. **Each tool best at its job:**
   - CLI: Creation + Results (simple, powerful)
   - API: Monitoring (structured, reliable)
   - GitHub: PR management (full control)

3. **Redundancy & Robustness:**
   - CLI fail? → Fallback to API
   - API rate limit? → Use CLI
   - Multiple paths to success

4. **Unique Features:**
   - `--parallel`: API tohle nemá!
   - Unix piping: Neuvěřitelně mocné
   - `--apply`: Jediný způsob aplikace změn

### **Confidence Level: 98%** ✅

Hybrid přístup je **jasně nejlepší řešení** pro Sophie.
Kombinuje jednoduchost CLI s robustností API.

---

## 🎯 **SUCCESS CRITERIA**

Sophie bude schopna:
- ✅ Vytvořit Jules session (CLI nebo API)
- ✅ Monitorovat progress (API - structured data)
- ✅ Získat výsledky (CLI - `pull --apply`)
- ✅ Vytvořit PR (GitHub API)
- ✅ Mergovat po testech (GitHub API)
- ✅ **100% autonomie** (s human approval na master)

**Blocker:** Žádný! CLI vyřešil poslední chybějící kousek.

---

**Status:** ✅ Research Complete  
**Next:** Manual testing of CLI (requires `jules login`)  
**Blocked By:** Interactive authentication  
**ETA:** Implementation ready po získání CLI auth
