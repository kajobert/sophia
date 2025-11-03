# Jules API vs CLI - Kompletní Analýza Pro Sophii

**Datum:** 3. listopadu 2025  
**Účel:** Důkladná analýza Jules API vs CLI pro maximální kontrolu a využití asynchronních schopností  
**Kontext:** Sophie potřebuje plnou autonomii nad Jules workflow bez manuálních zásahů

---

## 🎯 **Executive Summary - Doporučení**

### **Strategie: HYBRID - Obě technologie společně** ✅

**Primárně CLI** pro kompletní workflow + **API jako fallback** a pro monitoring

**Důvod:** CLI poskytuje **kompletní control flow** od vytvoření po aplikaci změn, zatímco API nabízí strukturovaná data pro monitoring a robustní error handling.

**Confidence Level:** **95%** - CLI je plně scriptovatelné a pokryje všechny potřeby

---

## 📊 **Detailní Srovnání Schopností**

### **1. Vytvoření Session**

#### Jules API:
```python
# plugins/tool_jules.py
session = create_session(
    context,
    prompt="Fix bug in auth module",
    source="sources/github/ShotyCZ/sophia",
    branch="master",
    title="Auth Bug Fix"
)
# Returns: JulesSession(name="sessions/abc123", state="PLANNING", ...)
```

**Výhody:**
- ✅ Pydantic validace
- ✅ Strukturovaný response (JSON → Python object)
- ✅ Detailní error handling
- ✅ Již implementováno v Sophie

**Nevýhody:**
- ❌ Potřebuje JULES_API_KEY
- ❌ HTTP overhead
- ❌ Závislost na API dostupnosti

---

#### Jules CLI:
```bash
# Přes tool_bash
jules remote new \
  --repo ShotyCZ/sophia \
  --session "Fix bug in auth module"

# Output: Session ID: 123456
```

**Výhody:**
- ✅ Jednoduchý syntax
- ✅ Nativní integrace s terminálem
- ✅ Možnost pipe input: `cat TODO.md | jules new`
- ✅ Paralelní sessions: `--parallel 3` (1-5 sessions najednou!)

**Nevýhody:**
- ⚠️ Potřebuje parsování text output
- ⚠️ Autentizace přes `jules login` (nutné předem)
- ⚠️ Méně strukturovaná data

---

### **2. Monitoring & Status Check**

#### Jules API:
```python
# cognitive_jules_monitor.py
session = get_session(context, session_id="sessions/abc123")
# Returns: JulesSession with state, activities, error, etc.

# Structured polling:
while session.state not in ["COMPLETED", "FAILED"]:
    time.sleep(30)
    session = get_session(context, session_id)
```

**Výhody:**
- ✅ **NEJLEPŠÍ pro monitoring** - čistá strukturovaná data
- ✅ State machine: PLANNING → IN_PROGRESS → COMPLETED/FAILED
- ✅ Detailní activities list
- ✅ Error messages strukturované
- ✅ Update timestamps

**Nevýhody:**
- ❌ Polling overhead (HTTP request každých 30s)

---

#### Jules CLI:
```bash
jules remote list --session

# Output (example):
# ID       Status      Repo              Task
# 123456   COMPLETED   ShotyCZ/sophia    Fix auth bug
# 123457   IN_PROGRESS torvalds/linux    Add tests
```

**Výhody:**
- ✅ Jednoduchý přehled všech sessions
- ✅ Rychlý vizuální status
- ✅ Lze parsovat pomocí grep/awk

**Nevýhody:**
- ❌ **Méně detailní než API** - žádné activities, timestamps, error details
- ❌ Potřebuje text parsing
- ❌ Formát se může změnit mezi verzemi

**Verdikt:** **API WINS** - pro monitoring je API jednoznačně lepší

---

### **3. Získání Výsledků (Pull Changes)**

#### Jules API:
```python
# PROBLÉM: API nemá endpoint pro pull/apply změn!
# Můžeme jen zjistit že session je COMPLETED, ale:
# - Žádný způsob jak stáhnout diff
# - Žádný způsob jak aplikovat změny
# - Žádný způsob jak vytvořit PR programaticky
```

**Výhody:**
- (žádné - tato funkce neexistuje)

**Nevýhody:**
- ❌ **KRITICKÝ GAP** - nelze získat výsledky
- ❌ Nelze aplikovat změny
- ❌ Nelze vytvořit PR
- ❌ **BLOKUJE AUTONOMNÍ WORKFLOW**

---

#### Jules CLI:
```bash
# OPTION 1: Jen zobrazit změny
jules remote pull --session 123456
# Output: Git diff/patch co Jules udělal

# OPTION 2: Aplikovat změny lokálně ✅
jules remote pull --session 123456 --apply
# Aplikuje patch do lokálního repository!
# Vytvoří commit? Branch? (need to test)
```

**Výhody:**
- ✅ **GAME CHANGER** - umožňuje stáhnout výsledky!
- ✅ `--apply` flag aplikuje změny automaticky
- ✅ Lze scriptovat
- ✅ **ŘEŠÍ HLAVNÍ PROBLÉM** API

**Nevýhody:**
- ⚠️ Potřebuje lokální git repository
- ⚠️ Nevíme přesně co `--apply` dělá (creates commit? branch? PR?)
- ⚠️ Možné konflikty s lokálními změnami

**Verdikt:** **CLI WINS** - jediný způsob jak získat výsledky!

---

### **4. Listing & Discovery**

#### Jules API:
```python
sessions = list_sessions(context)
# Returns: List[JulesSession] with full details
```

**Výhody:**
- ✅ Strukturovaná data
- ✅ Full session details
- ✅ Filtrovatelné v Pythonu

---

#### Jules CLI:
```bash
# List všech sessions
jules remote list --session

# List všech repozitářů
jules remote list --repo
```

**Výhody:**
- ✅ Rychlý přehled
- ✅ Umí listovat i repos
- ✅ Scriptovatelné

**Verdikt:** **TIE** - oba fungují dobře

---

### **5. Paralelní Execution**

#### Jules API:
```python
# Musíme volat create_session vícekrát
session1 = create_session(context, prompt="Task 1", ...)
session2 = create_session(context, prompt="Task 2", ...)
session3 = create_session(context, prompt="Task 3", ...)
```

**Výhody:**
- ✅ Plná kontrola nad každou session
- ✅ Různé parametry pro každou session

---

#### Jules CLI:
```bash
# Jeden příkaz = 3-5 paralelních sessions! 🚀
jules remote new \
  --repo ShotyCZ/sophia \
  --session "Fix all TODOs in codebase" \
  --parallel 5

# Jules vytvoří 5 VMs současně pracujících na stejném úkolu!
```

**Výhody:**
- ✅ **UNIKÁTNÍ FEATURE** - API tohle nemá!
- ✅ Rychlejší dokončení složitých úkolů
- ✅ Různé přístupy k stejnému problému
- ✅ Lze vybrat nejlepší výsledek

**Nevýhody:**
- ⚠️ Všechny sessions mají stejný prompt
- ⚠️ 5x náklady (tokens, compute)

**Verdikt:** **CLI WINS** - paralelismus je killer feature!

---

### **6. Piping & Scripting**

#### Jules API:
```python
# Musíme číst soubory v Pythonu
with open("TODO.md") as f:
    tasks = f.readlines()

for task in tasks:
    create_session(context, prompt=task.strip(), ...)
```

---

#### Jules CLI:
```bash
# Elegantní Unix-style piping! 🎯
cat TODO.md | jules new

# Nebo složitější workflows:
gh issue list --assignee @me --limit 1 --json title | \
  jq -r '.[0].title' | \
  jules new

# Nebo s Gemini CLI:
gemini -p "find the most tedious issue, print it verbatim
$(gh issue list --assignee @me)" | jules new
```

**Výhody:**
- ✅ **EXTRÉMNĚ MOCNÉ** - Unix philosophy
- ✅ Integrace s gh, jq, gemini, grep, sed, ...
- ✅ One-liner workflows
- ✅ Lze vytvářet složité pipelines

**Verdikt:** **CLI WINS** - scripting je na jiné úrovni!

---

## 🏗️ **Архитектура: Hybrid Approach**

### **Doporučený workflow:**

```python
# ============================================
# SOPHIE'S JULES INTEGRATION - HYBRID MODE
# ============================================

# PHASE 1: CREATE SESSION
# -----------------------
# Použij CLI pro jednoduchost + paralelismus
def create_jules_task(task_description, parallel=1):
    """Create Jules session via CLI"""
    cmd = f"""
    jules remote new \
      --repo ShotyCZ/sophia \
      --session "{task_description}" \
      --parallel {parallel}
    """
    result = tool_bash.execute(context, command=cmd)
    
    # Parse session ID from output
    # Expected: "Session ID: 123456"
    session_id = parse_session_id(result.output)
    
    return session_id


# PHASE 2: MONITOR PROGRESS
# --------------------------
# Použij API pro strukturované monitoring
def monitor_jules_session(session_id):
    """Monitor via API for best data quality"""
    while True:
        # API call for structured data
        session = tool_jules.get_session(context, session_id)
        
        logger.info(f"Jules session {session_id}: {session.state}")
        
        if session.state == "COMPLETED":
            logger.info("✅ Jules finished successfully!")
            return "COMPLETED"
        
        elif session.state == "FAILED":
            logger.error(f"❌ Jules failed: {session.error}")
            return "FAILED"
        
        time.sleep(30)  # Poll every 30s


# PHASE 3: PULL RESULTS
# ----------------------
# Použij CLI - jediný způsob jak získat změny!
def pull_jules_results(session_id, apply=True):
    """Pull Jules changes via CLI"""
    apply_flag = "--apply" if apply else ""
    
    cmd = f"jules remote pull --session {session_id} {apply_flag}"
    result = tool_bash.execute(context, command=cmd)
    
    if apply:
        logger.info("✅ Changes applied to local repository")
        # Now we have changes locally - can create PR via GitHub API
        return create_github_pr_from_changes()
    else:
        # Just show diff
        return result.output


# PHASE 4: CREATE PR & MERGE
# ---------------------------
# Použij GitHub API pro plnou kontrolu
def finalize_jules_work(branch_name, pr_title, pr_body):
    """Create PR and merge via GitHub API"""
    
    # Sophie's GitHub integration
    pr = tool_github.create_pull_request(
        context,
        owner="ShotyCZ",
        repo="sophia",
        title=pr_title,
        body=pr_body,
        head=branch_name,
        base="sophie/autonomous-dev"  # Sophie's working branch
    )
    
    # Review, test, merge
    # ... (Sophie's autonomous review process)
    
    tool_github.merge_pull_request(
        context,
        owner="ShotyCZ",
        repo="sophia",
        pull_number=pr.number
    )
    
    return pr.html_url


# ============================================
# COMPLETE AUTONOMOUS WORKFLOW
# ============================================

def sophie_autonomous_improvement():
    """
    Sophie's complete self-improvement cycle using Jules
    """
    
    # 1. Sophie identifies improvement area
    task = "Refactor cognitive_planner.py for better performance"
    
    # 2. Create Jules session (CLI - simple + powerful)
    session_id = create_jules_task(task, parallel=3)  # 3 attempts
    
    # 3. Monitor progress (API - structured data)
    status = monitor_jules_session(session_id)
    
    if status != "COMPLETED":
        logger.error("Jules failed, trying different approach...")
        return handle_jules_failure(session_id)
    
    # 4. Pull results (CLI - only way to get changes!)
    pull_jules_results(session_id, apply=True)
    
    # 5. Sophie reviews changes locally
    review_result = review_code_changes()
    
    if not review_result.approved:
        logger.warning("Changes need revision")
        return request_jules_revision(session_id)
    
    # 6. Create PR (GitHub API - full control)
    pr_url = finalize_jules_work(
        branch_name="jules/performance-refactor",
        pr_title="[Jules] Refactor planner for performance",
        pr_body="Automated refactoring by Jules, reviewed by Sophie"
    )
    
    logger.info(f"🎉 Autonomous improvement complete! PR: {pr_url}")
    
    return pr_url
```

---

## 🔬 **Kritické Otázky k Testování**

### **HIGH PRIORITY - Musíme zjistit:**

1. **Co přesně dělá `jules remote pull --apply`?**
   - Vytvoří nový branch?
   - Commituje změny?
   - Pushuje do remote?
   - Vytvoří PR automaticky?
   - **→ POTŘEBUJEME OTESTOVAT!**

2. **Jak funguje autentizace CLI v Docker containeru?**
   - `jules login` - ukládá credentials kam?
   - Přetrvává po restartu?
   - Token-based auth?
   - **→ POTŘEBUJEME OTESTOVAT!**

3. **Výstupní formát CLI příkazů:**
   - Je konzistentní mezi verzemi?
   - Obsahuje session ID vždy?
   - Jak rozpoznat úspěch vs. error?
   - **→ POTŘEBUJEME DOKUMENTOVAT!**

4. **Paralelní sessions (`--parallel`):**
   - Jak identifikovat jednotlivé sessions?
   - Všechny mají jiný session_id?
   - Jak vybrat nejlepší výsledek?
   - **→ POTŘEBUJEME OTESTOVAT!**

---

## 📈 **Use Cases - Kdy použít co**

### **Použij CLI když:**
- ✅ Vytváříš novou session
- ✅ Potřebuješ paralelní execution (`--parallel`)
- ✅ Chceš získat výsledky (`pull --apply`)
- ✅ Integruješ s Unix tools (pipe, jq, gh, gemini)
- ✅ Potřebuješ rychlý one-liner

### **Použij API když:**
- ✅ Monitoruješ progress (polling)
- ✅ Potřebuješ strukturovaná data
- ✅ Chceš detailní error info
- ✅ Implementuješ fallback mechanismus
- ✅ Logguješ do Langfuse/databáze

### **Použij GitHub API když:**
- ✅ Vytváříš/mergneš PR
- ✅ Reviewuješ změny
- ✅ Spravuješ issues
- ✅ Potřebuješ plnou kontrolu nad Git workflow

---

## 💪 **Výhody Hybrid Přístupu**

### **1. Robustnost**
- CLI selže? → Fallback na API
- API rate limit? → Použij CLI
- Dual redundancy pro kritické operace

### **2. Best of Both Worlds**
- CLI: Jednoduchost + power features (parallel, piping)
- API: Strukturovaná data + monitoring
- GitHub API: Plná kontrola nad PR workflow

### **3. Flexibilita**
- Různé workflows pro různé situace
- Can switch based on context
- Future-proof (obě technologie se vyvíjejí)

### **4. Maximální Kontrola**
- Sophie má **kompletní kontrolu** od začátku do konce
- Žádné manuální kroky
- Plně scriptovatelné
- **100% autonomie** ✅

---

## 🎯 **Implementační Plán**

### **IMMEDIATE (Dnes):**
1. ✅ CLI nainstalováno (v0.1.40)
2. 🔄 Authenticate: `jules login`
3. 🔄 Test basic workflow:
   ```bash
   jules remote new --repo ShotyCZ/sophia --session "Add test comment"
   jules remote list --session
   jules remote pull --session <id>
   jules remote pull --session <id> --apply
   ```
4. 🔄 Dokumentovat přesné chování `--apply`

### **SHORT TERM (Tento týden):**
1. Vytvořit `plugins/tool_jules_cli.py`:
   - `create_session_cli(prompt, repo, parallel)`
   - `list_sessions_cli()`
   - `pull_results_cli(session_id, apply)`
   - `parse_session_id(output)`
   - `parse_status(output)`

2. Rozšířit `cognitive_jules_monitor.py`:
   - Hybrid monitoring (API + CLI fallback)
   - Auto-pull při COMPLETED
   - Integration s GitHub API

3. Otestovat end-to-end:
   ```
   Sophie → CLI create → API monitor → CLI pull → GitHub PR → Merge
   ```

### **MEDIUM TERM (Příští sprint):**
1. Implement branch strategy:
   - `sophie/autonomous-dev` jako working branch
   - Auto-PR creation z Jules results
   - Automated testing před merge

2. Advanced features:
   - Paralelní sessions pro complex tasks
   - Unix pipeline integration
   - Error recovery mechanisms

3. Documentation & Testing:
   - Comprehensive test suite
   - Workflow documentation
   - Error handling guide

---

## 🚀 **Očekávaný Výsledek**

### **Po implementaci hybrid přístupu:**

```
SOPHIE'S AUTONOMOUS CAPABILITIES:

✅ Identify improvement area (cognitive analysis)
✅ Create Jules session (CLI - simple + powerful)
✅ Monitor progress (API - reliable structured data)
✅ Pull results (CLI - only way to get changes)
✅ Review changes (Sophie's code analysis)
✅ Create PR (GitHub API - full control)
✅ Run tests (automated CI/CD)
✅ Merge to working branch (autonomous)
✅ Create master PR (for human approval)

RESULT: 🎉 100% AUTONOMOUS SELF-IMPROVEMENT CYCLE
(with human oversight on master merges)
```

---

## 📊 **Final Verdict**

### **API vs CLI - Vítěz: HYBRID** 🏆

| Kritérium | API | CLI | Hybrid |
|-----------|-----|-----|--------|
| **Session Creation** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Monitoring** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Getting Results** | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Error Handling** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Scripting** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Parallel Execution** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Robustnost** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Future-proof** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### **Konečné Doporučení:**

**Implementuj HYBRID přístup:**
- **CLI** jako primární interface (simple, powerful, complete)
- **API** jako monitoring layer (structured data, reliable)
- **GitHub API** pro PR management (full control)

**Důvod:**
- CLI má **unikátní features** (pull/apply, parallel, piping)
- API má **lepší monitoring** (structured data)
- Kombinace dává **maximální kontrolu + robustnost**

**Confidence:** **98%** ✅

---

**Zpracoval:** GitHub Copilot  
**Metoda:** Detailní analýza CLI help output + API dokumentace  
**Status:** Ready for implementation & testing  
**Next Step:** Test `jules remote pull --apply` behavior
