# 🎭 Jules Orchestrator - Implementační Plán
**Datum:** 2025-11-03  
**Autor:** Robert + Sophia AI  
**Status:** Planning Phase  

---

## 📋 **Executive Summary**

Vytvoření systému **Jules Orchestrator**, který umožní Sophii delegovat úkoly na specializované Jules instance běžící v oddělených Git branches. Každý Jules worker má přístup k Gemini 2.5 Pro (100 dotazů/den zdarma), což multiplikuje výpočetní kapacitu a token limity.

---

## 🎯 **Cíle Projektu**

### **Primary Goals:**
1. ✅ **Token Multiplikace** - využít N × 100 free dotazů/den
2. ✅ **Specializace** - každý Jules má vlastní doménu (web/code/data)
3. ✅ **Bezpečnost** - izolace v samostatných branches, merge pouze po review
4. ✅ **Orchestrace** - Sophia rozhoduje, kdy delegovat vs. řešit lokálně

### **Success Metrics:**
- [ ] 3+ funkční Jules workers v samostatných branches
- [ ] Routing logic správně alokuje úkoly
- [ ] Token savings >50% na complex tasks
- [ ] Zero unauthorized merges do master

---

## 🏗️ **Architektura**

### **1. Git Branch Struktur**

```
master (protected)
├── feature/jules-api-integration (current work)
└── nomad/ (Jules workspace - isolated)
    ├── web-explorer/
    │   ├── tools/ (playwright, tavily, sumarizace)
    │   └── context/ (web scraping specializace)
    ├── code-sandbox/
    │   ├── tools/ (pytest, black, mypy)
    │   └── context/ (Python testing & debugging)
    └── data-analyst/
        ├── tools/ (pandas, plotly, estadística)
        └── context/ (data analysis & viz)
```

### **2. Plugin Architektura**

```python
# plugins/tool_jules_orchestrator.py
class JulesOrchestrator(BasePlugin):
    """
    Orchestrates delegation of tasks to specialized Jules workers.
    
    Responsibilities:
    - Analyze task complexity & domain
    - Select appropriate Jules worker (or handle locally)
    - Monitor Jules execution via API
    - Merge results back to context
    - Safety checks before git operations
    """
    
    def __init__(self):
        self.workers = {
            "web_explorer": JulesWorker(
                branch="nomad/web-explorer",
                specialization="web_scraping_research",
                tools=["playwright", "tavily", "summarization"]
            ),
            "code_sandbox": JulesWorker(
                branch="nomad/code-sandbox", 
                specialization="python_testing_debug",
                tools=["pytest", "black", "mypy"]
            ),
            "data_analyst": JulesWorker(
                branch="nomad/data-analyst",
                specialization="data_analysis_viz",
                tools=["pandas", "plotly", "statistics"]
            )
        }
        
        self.router = TaskRouter()  # Decides local vs Jules
        self.safety = SafetyWrapper()  # Git & merge validation
```

### **3. Task Routing Logic**

```python
class TaskRouter:
    """
    Analyzes tasks and routes to optimal executor.
    
    Decision Tree:
    1. Cost estimate (tokens needed)
    2. Specialization match
    3. Jules availability (daily quota)
    4. Task complexity score
    
    Output: Executor("local" | "jules:web_explorer" | ...)
    """
    
    def route_task(self, task: Task) -> str:
        # Cost > 10k tokens → Jules (Gemini 2.5 Pro free)
        # Domain = web → Jules:web_explorer
        # Domain = code → Jules:code_sandbox
        # Simple query → Sophia (cheap model)
        pass
```

### **4. Jules Worker Spec**

```python
class JulesWorker:
    """
    Represents a single Jules instance in a dedicated branch.
    
    Lifecycle:
    1. Checkout branch (git worktree if parallel)
    2. Send task via Jules API
    3. Monitor execution (streaming logs)
    4. Collect results
    5. Create PR to feature branch (not master!)
    6. Sophia reviews & merges
    """
    
    def __init__(self, branch: str, specialization: str, tools: list):
        self.branch = branch
        self.specialization = specialization
        self.tools = tools
        self.api_client = JulesAPIClient()
        
    async def execute_task(self, prompt: str) -> JulesResult:
        # 1. Ensure branch exists & is clean
        # 2. Call Jules API with specialized context
        # 3. Stream logs to Sophia
        # 4. Return result + git changes
        pass
```

---

## 📦 **Implementation Phases**

### **Phase 1: Foundation (Week 1)**
**Goal:** Basic Jules Orchestrator plugin + single worker

**Tasks:**
- [ ] Create `plugins/tool_jules_orchestrator.py`
- [ ] Implement `JulesWorker` class with API integration
- [ ] Create `nomad/web-explorer` branch with tools
- [ ] Basic routing: simple queries local, complex → Jules
- [ ] Safety wrapper: validate git operations
- [ ] Unit tests for routing logic

**Deliverables:**
- Working Jules worker in `nomad/web-explorer`
- Sophia can delegate 1 task type to Jules
- All git ops are safe (no master writes)

---

### **Phase 2: Multi-Worker System (Week 2)**
**Goal:** 3 specialized workers + smart routing

**Tasks:**
- [ ] Create `nomad/code-sandbox` branch
- [ ] Create `nomad/data-analyst` branch
- [ ] Implement `TaskRouter` with cost estimation
- [ ] Add specialization matching algorithm
- [ ] Jules quota tracking (100/day limit per worker)
- [ ] Parallel execution support (git worktree)
- [ ] Integration tests

**Deliverables:**
- 3 workers: web, code, data
- Router correctly allocates tasks
- Quota tracking prevents over-use

---

### **Phase 3: Advanced Features (Week 3)**
**Goal:** Production-ready with monitoring

**Tasks:**
- [ ] Result caching (avoid duplicate Jules calls)
- [ ] Fallback logic (Jules quota exhausted → local)
- [ ] Performance metrics dashboard
- [ ] Cost analysis (tokens saved via Jules)
- [ ] Auto-merge for safe changes (tests pass)
- [ ] Rollback mechanism on failures
- [ ] Documentation & examples

**Deliverables:**
- Production-ready orchestrator
- Metrics showing token/cost savings
- Full documentation

---

## 🔒 **Security & Safety**

### **Git Safety Rules:**
1. ✅ Jules NEVER writes to `master` directly
2. ✅ All Jules changes → PR to `feature/*` branch
3. ✅ Sophia reviews diffs before merge
4. ✅ Automated tests must pass
5. ✅ Rollback available for any Jules change

### **API Safety:**
```python
class SafetyWrapper:
    def validate_git_operation(self, operation: GitOp) -> bool:
        # Block: writes to master
        # Block: force pushes
        # Block: deletion of critical files
        # Allow: PR creation to feature branches
        pass
    
    def review_jules_changes(self, diff: str) -> ReviewResult:
        # Static analysis of changes
        # Test coverage check
        # Sophia LLM review of diff
        # Human approval for risky changes
        pass
```

---

## 📊 **Monitoring & Metrics**

### **Key Metrics:**
- **Token Usage:** local vs Jules, cost savings
- **Task Distribution:** % delegated to each worker
- **Success Rate:** Jules task completion %
- **Quota Utilization:** daily limit tracking
- **Response Time:** local vs Jules latency

### **Dashboard:**
```
╭─────────────── JULES ORCHESTRATOR STATUS ───────────────╮
│ Workers Active: 3/3                                     │
│                                                          │
│ 🌐 web-explorer    ████████░░ 80/100 queries today      │
│ 💻 code-sandbox    ███░░░░░░░ 30/100 queries today      │
│ 📊 data-analyst    █████░░░░░ 50/100 queries today      │
│                                                          │
│ Today's Stats:                                          │
│   Tasks Delegated: 45                                   │
│   Tokens Saved: 1,250,000 (~$2.50)                      │
│   Success Rate: 97.8%                                   │
╰──────────────────────────────────────────────────────────╯
```

---

## 🧪 **Testing Strategy**

### **Unit Tests:**
- [ ] TaskRouter logic (cost estimation)
- [ ] JulesWorker API calls (mocked)
- [ ] SafetyWrapper git validation
- [ ] Quota tracking accuracy

### **Integration Tests:**
- [ ] End-to-end: Sophia → Jules → Result
- [ ] Multi-worker parallel execution
- [ ] Fallback when quota exhausted
- [ ] PR creation & merge flow

### **Manual Tests:**
- [ ] Real web scraping task → Jules:web_explorer
- [ ] Python debugging → Jules:code_sandbox
- [ ] Data analysis → Jules:data_analyst
- [ ] Safety: attempt master write (should block)

---

## 📚 **Dependencies**

### **Required:**
- ✅ `tool_jules.py` (existing Jules API plugin)
- ✅ Git worktree support (parallel branches)
- ⚠️ GitHub API (PR creation automation)
- ⚠️ Cost tracking infrastructure

### **Optional:**
- 🔄 Langfuse integration (Jules task logging)
- 🔄 WebUI dashboard for monitoring

---

## 🚀 **Rollout Plan**

### **Soft Launch (Internal Testing):**
1. Deploy Phase 1 to `feature/jules-orchestrator`
2. Test with robert-notes.txt summarization
3. Validate git safety (no master writes)
4. Monitor for 1 week

### **Production Deployment:**
1. Merge to master after review
2. Enable for all users
3. Monitor metrics daily
4. Iterate based on feedback

---

## 🎓 **Lessons Learned (Pre-Implementation)**

### **From TUI Debugging:**
❌ **DON'T:** Start coding without detailed plan  
✅ **DO:** Brainstorm → Plan → Review → Implement  

❌ **DON'T:** Assume existing systems work as expected  
✅ **DO:** Validate assumptions with tests first  

❌ **DON'T:** Mix multiple concerns (UI + routing)  
✅ **DO:** One feature at a time, fully tested  

---

## 📝 **Next Steps**

1. **Review this plan** - Robert approval needed
2. **Create Jules worker branches** - git setup
3. **Implement Phase 1** - basic orchestrator
4. **Test thoroughly** - no surprises!
5. **Iterate** - based on real-world usage

---

## 🤔 **Open Questions**

1. **Jules API rate limits?** - Does Jules have per-session limits beyond 100/day?
2. **Git worktree vs checkout?** - Best way to manage parallel branches?
3. **Result format?** - How does Jules return structured data?
4. **Context size?** - Max tokens Jules can handle in single task?
5. **Streaming?** - Can we stream Jules progress to Sophia in real-time?

---

**Status:** ✅ Plan Complete - Awaiting Review & Approval
