# 🌙 NOČNÍ JULES WORKERS - QUICK START GUIDE

**Datum:** 3. listopadu 2025  
**Status:** ⚠️ Připraveno, čeká na Jules API key

---

## ⚠️ **DŮLEŽITÉ: Jules API Key**

Jules workers vyžadují `JULES_API_KEY` v environment variables.

### **Možnost A: Máte Jules API key**

1. **Nastavte API key:**
   ```bash
   export JULES_API_KEY="your-api-key-here"
   ```

2. **Spusťte všechny 4 workery:**
   ```bash
   cd /workspaces/sophia
   python scripts/launch_night_workers.py
   ```

3. **Jděte spát!** 💤
   - Ráno (9:00 AM) zkontrolujte `docs/JULES_ACTIVE_SESSIONS.md`
   - Review Jules commits na nomad/* branches

---

### **Možnost B: Nemáte Jules API key (ALTERNATIVA)**

Máme připravené **detailní task files** které můžete:

1. **Použít ručně** s ChatGPT/Claude/Gemini
2. **Rozdělit mezi více AI asistentu** paralelně
3. **Dát Copilotu** v tomto chatu

---

## 📋 **4 PŘIPRAVENÉ ÚKOLY**

### **Task #1: Rich Library Research** (HIGH priority)
**File:** `docs/tasks/JULES_TASK_RICH_RESEARCH.md`

**Co udělat:**
1. Prostuduj Rich library dokumentaci
2. Najdi 5+ production příkladů
3. Analyzuj sticky panel patterns
4. Vytvoř improvement recommendations

**Deliverables:**
- `docs/research/RICH_BEST_PRACTICES.md`
- `docs/research/RICH_PRODUCTION_EXAMPLES.md`  
- `docs/research/SCIFI_UI_IMPROVEMENTS.md`

**Spuštění manuálně:**
```bash
# Copilot prompt
"Read docs/tasks/JULES_TASK_RICH_RESEARCH.md and complete all tasks.
Create the deliverable files as specified."
```

---

### **Task #2: AI UX Trends Analysis** (MEDIUM priority)
**File:** `docs/tasks/JULES_TASK_UX_TRENDS.md`

**Co udělat:**
1. Research Claude, ChatGPT, Cursor, Replit Agent UIs
2. Identifikuj common UX patterns
3. Gap analysis: co nám chybí
4. Priority roadmap

**Deliverables:**
- `docs/research/AI_UX_TRENDS_2025.md`
- `docs/research/COMPETITIVE_ANALYSIS.md`
- `docs/research/SOPHIA_UX_ROADMAP.md`

**Spuštění manuálně:**
```bash
# Web search required - use Tavily or manual browsing
```

---

### **Task #3: GitHub TUI Gems** (HIGH priority)
**File:** `docs/tasks/JULES_TASK_GITHUB_GEMS.md`

**Co udělat:**
1. Search GitHub for top TUI projects (500+ stars)
2. Analyze top 5 repositories
3. Extract reusable code patterns
4. Create integration plan

**Deliverables:**
- `docs/research/GITHUB_TUI_GEMS.md`
- `docs/research/CODE_PATTERNS_TO_STEAL.md`
- `scripts/examples/` (working demos)
- `docs/research/INTEGRATION_PLAN.md`

**Spuštění manuálně:**
```bash
# GitHub search queries included in task file
```

---

### **Task #4: Documentation Audit** (MEDIUM priority)
**File:** `docs/tasks/JULES_TASK_DOCS_AUDIT.md`

**Co udělat:**
1. Přečti VŠECHNY docs/ soubory
2. Gap analysis - co chybí
3. Quality assessment
4. Reorganization plan

**Deliverables:**
- `docs/audit/DOCUMENTATION_AUDIT.md`
- `docs/audit/DOCUMENTATION_REORGANIZATION_PLAN.md`
- `docs/audit/PRIORITY_DOCS_TO_WRITE.md`
- `docs/templates/` (šablony)

**Spuštění manuálně:**
```bash
# Copilot prompt
"Read docs/tasks/JULES_TASK_DOCS_AUDIT.md and audit all our documentation.
Complete all deliverables."
```

---

## 🤖 **ALTERNATIVA: Použij Copilot TEĎKA**

Můžeš dát úkoly Copilotu v tomto chatu:

```
@workspace Přečti si docs/tasks/JULES_TASK_RICH_RESEARCH.md 
a dokončit všechny úkoly. Vytvoř deliverable files jak je specifikováno.
```

**Výhody:**
- Okamžitý start (nepotřebuješ Jules API)
- Můžeš kontrolovat průběžně
- Copilot má přístup k workspace

**Nevýhody:**
- Nepracuje autonomně během spánku
- Musíš být online

---

## 📊 **EXPECTED OUTCOMES**

**Do rána (nebo po dokončení):**
- 📚 4x comprehensive research documents
- 💡 15-20 konkrétních improvement návrhů
- 🔍 10+ reusable code patterns discovered
- 📈 Priority roadmap pro další development

**Token usage estimate:**
- Rich Research: ~50 Gemini sessions
- UX Trends: ~40 sessions (web search heavy)
- GitHub Gems: ~45 sessions
- Docs Audit: ~35 sessions
- **Total: ~170 free sessions**

---

## 🎯 **DOPORUČENÍ**

**Pokud máš Jules API:**
✅ Použij automated launch - jdi spát v klidu

**Pokud nemáš Jules API:**
1. ✅ **Task #1 (Rich Research)** - dej Copilotu TEĎKA (highest impact)
2. ✅ **Task #3 (GitHub Gems)** - dej Copilotu TEĎKA (quick wins)
3. 🔄 **Task #2 (UX Trends)** - můžeš udělat ráno sám (web browsing)
4. 🔄 **Task #4 (Docs Audit)** - můžeš udělat odpoledne (nice-to-have)

---

## 💬 **COPILOT PROMPTS READY TO USE**

### **Prompt #1: Rich Research (15 min)**
```
@workspace Read docs/tasks/JULES_TASK_RICH_RESEARCH.md completely.

Your task:
1. Study Rich library documentation (GitHub: Textualize/rich)
2. Find 5+ production examples of sticky panels with Live mode
3. Analyze their approach to Layout + Text accumulation
4. Create all 3 deliverable files:
   - docs/research/RICH_BEST_PRACTICES.md
   - docs/research/RICH_PRODUCTION_EXAMPLES.md
   - docs/research/SCIFI_UI_IMPROVEMENTS.md

Focus on solving our sticky panel problem in interface_terminal_scifi.py.
Include code examples and concrete recommendations.
```

### **Prompt #2: GitHub Gems (20 min)**
```
@workspace Read docs/tasks/JULES_TASK_GITHUB_GEMS.md completely.

Your task:
1. Search GitHub for top TUI projects (Python, Rich library, 500+ stars)
2. Analyze top 5 repositories - architecture, patterns, tricks
3. Extract 10+ reusable code patterns
4. Create all deliverables:
   - docs/research/GITHUB_TUI_GEMS.md
   - docs/research/CODE_PATTERNS_TO_STEAL.md
   - docs/research/INTEGRATION_PLAN.md
   - scripts/examples/ (working demos)

Prioritize patterns that solve sticky panels and Live refresh issues.
```

---

**Ready to launch! 🚀**  
**Choose your path: Automated Jules workers OR Manual Copilot execution**
