# Sophia 2.0: Critical Questions & Decisions Required

**Date:** November 3, 2025  
**Status:** 🔴 BLOCKING - Implementation Cannot Proceed Without Answers  
**Estimated Reading Time:** 10 minutes  

---

## 🎯 TL;DR

Sophia má solidní základ (MVP fáze 1-3 hotové), ale k plné autonomii chybí:
1. **Continuous loop** (neblokující smyčka)
2. **Task queue & scheduler** (správa úkolů)
3. **Memory consolidation** ("snění")
4. **Autonomous self-improvement** (automatické sledování roberts-notes.txt)
5. **State persistence** (crash recovery)

**Vytvořil jsem kompletní roadmapu** v `/docs/en/AUTONOMOUS_MVP_ROADMAP.md`

**Ale potřebuji tvé odpovědi** na níže uvedené otázky, abych mohl začít implementovat.

---

## ❓ KRITICKÉ OTÁZKY PRO TEBE

### 🔐 Kategorie 1: Bezpečnost & Autonomie

#### Q1: Může Sophia autonomně mergovat do `master` větve?
**Kontext:** Sophia může vytvářet feature branches, testovat kód, vytvářet PR.

**Možnosti:**
- **A)** ❌ NE - Master vždy vyžaduje lidské schválení (DOPORUČUJI)
- **B)** ✅ ANO - Ale pouze pokud projde CI/CD a má 100% test coverage
- **C)** ⚖️ ČÁSTEČNĚ - Může mergovat "bezpečné" změny (dokumentace, testy), ne core kód

**Tvá volba:** _____

**Dopad:** Určuje implementaci `cognitive_integrator` pluginu.

---

#### Q2: Jaká je maximální cena pro jeden autonomní úkol?
**Kontext:** Sophia bude delegovat úkoly Julesovi, volat LLM API, provádět benchmarky.

**Možnosti:**
- **A)** $0.50 per task
- **B)** $1.00 per task
- **C)** $5.00 per task
- **D)** Žádný limit, důvěřuji Sophie
- **E)** Jiná hodnota: $_____

**Tvá volba:** _____

**Dopad:** Hard limit v task queue, auto-abort drahých operací.

---

#### Q3: Potřebuješ "emergency stop" tlačítko v UI?
**Kontext:** Pokud Sophia dělá něco špatně/drahého, okamžitě zastavit.

**Možnosti:**
- **A)** ✅ ANO - UI button + CLI příkaz `/stop`
- **B)** ❌ NE - Stačí Ctrl+C
- **C)** ⚖️ Soft stop (dokončí aktuální úkol, pak zastaví)

**Tvá volba:** _____

**Dopad:** Implementace v interface pluginech, event system.

---

### 🧠 Kategorie 2: Paměť & Učení

#### Q4: Má být memory consolidation (snění) vždy aktivní?
**Kontext:** Po každé konverzaci Sophie analyzuje a ukládá klíčové poznatky do ChromaDB.

**Možnosti:**
- **A)** ✅ Vždy aktivní (automatická konsolidace každých 6 hodin)
- **B)** ❌ Opt-in per session (uživatel musí říct "remember this")
- **C)** ⚖️ Aktivní, ale s možností vypnout pro citlivé konverzace

**Tvá volba:** _____

**Dopad:** Trigger logika v `cognitive_memory_consolidator` pluginu.

---

#### Q5: Co NESMÍ být uloženo do long-term memory?
**Kontext:** Bezpečnost a privacy.

**Možnosti (vyber všechny, co platí):**
- [ ] API klíče a tokeny
- [ ] Absolutní cesty k souborům (/home/user/...)
- [ ] Hesla nebo credentials
- [ ] Osobní údaje uživatele (jména, emaily, ...)
- [ ] Obsah .env souborů
- [ ] Jiné: _____________________

**Tvá volba:** _____

**Dopad:** Filtrovací logika před uložením do ChromaDB.

---

#### Q6: Maximální velikost ChromaDB databáze?
**Kontext:** Long-term paměť může růst donekonečna a generovat náklady.

**Možnosti:**
- **A)** 100 MB
- **B)** 500 MB
- **C)** 1 GB
- **D)** 5 GB
- **E)** Bez limitu

**Tvá volba:** _____

**Dopad:** Garbage collection policy, stará data smazat nebo archivovat.

---

### 🎭 Kategorie 3: Osobnost & Prompty

#### Q7: Může Sophia autonomně měnit své system prompty?
**Kontext:** Učení z interakcí, optimalizace komunikačního stylu.

**Možnosti:**
- **A)** ✅ ANO - Ale pouze komunikační styl, NE DNA principy (doporučuji)
- **B)** ❌ NE - System prompty jsou immutable, pouze human může měnit
- **C)** ⚖️ ANO - Ale vyžaduje lidské schválení před aplikací

**Tvá volba:** _____

**Dopad:** Implementace `core_system_prompt_manager` pluginu.

---

#### Q8: Podporovat různé "persony" pro různé kontexty?
**Kontext:** Technický/přátelský/formální styl podle situace.

**Příklad:**
- Konverzace s uživatelem → Přátelská Sophie
- Code review → Technická Sophie
- Dokumentace → Formální Sophie

**Možnosti:**
- **A)** ✅ ANO - Context-aware personality switching
- **B)** ❌ NE - Jedna konzistentní personalita vždy
- **C)** ⚖️ Uživatel může vybrat preferovanou personu v settings

**Tvá volba:** _____

**Dopad:** Prompt management complexity, context detection.

---

#### Q9: Co když user preference konfliktuje s DNA?
**Kontext:** Uživatel chce agresivní styl, ale DNA říká "harmonia a compassion".

**Možnosti:**
- **A)** DNA vítězí vždy (principy jsou neměnné)
- **B)** User preference vítězí (personalita je služba)
- **C)** Sophie vysvětlí konflikt a nabídne kompromis

**Tvá volba:** _____

**Dopad:** Conflict resolution v personality manager.

---

### 🔧 Kategorie 4: Self-Improvement

#### Q10: Může Sophia modifikovat své vlastní Core (`core/*.py`)?
**Kontext:** Core je "sacred" dle architektury, ale co když chce vylepšit kernel?

**Možnosti:**
- **A)** ❌ NE - Core je locked, pouze pluginy lze měnit (DOPORUČUJI)
- **B)** ✅ ANO - Ale pouze s explicit human approval + extensive tests
- **C)** ⚖️ Může navrhovat změny v Core, ale nemůže je aplikovat

**Tvá volba:** _____

**Dopad:** Guardrails v `cognitive_self_improvement` pluginu.

---

#### Q11: Mandatory human review pro jaké typy změn?
**Kontext:** Některé změny jsou rizikovější než jiné.

**Možnosti (vyber všechny, co vyžadují review):**
- [ ] Bezpečnostní kód (authentication, permissions)
- [ ] Data handling (file I/O, database operations)
- [ ] Network operations (API calls, webhooks)
- [ ] Cost-critical operations (expensive LLM calls)
- [ ] Core architecture (kernel, plugin manager)
- [ ] Vše (100% human review)
- [ ] Nic (full autonomy)

**Tvá volba:** _____

**Dopad:** Auto-approval logic, PR tagging system.

---

#### Q12: Jak zabránit nekonečným self-improvement cyklům?
**Kontext:** Sophia může teoreticky stále vylepšovat tentýž kód dokola.

**Možnosti:**
- **A)** Max 1 improvement per feature per day
- **B)** Improvement pouze pokud benchmarks/metrics prokáží zlepšení
- **C)** Cooldown period (7 dní) po každé změně stejného souboru
- **D)** Kombinace B+C

**Tvá volba:** _____

**Dopad:** Rate limiting v self-improvement workflow.

---

### 💰 Kategorie 5: Resource Management

#### Q13: Denní/měsíční budget limit pro LLM API?
**Kontext:** Prevence před neočekávanými náklady.

**Daily Limit:**
- **A)** $5/day
- **B)** $10/day
- **C)** $20/day
- **D)** Bez denního limitu

**Monthly Limit:**
- **A)** $50/month
- **B)** $100/month
- **C)** $300/month
- **D)** Bez měsíčního limitu

**Tvá volba:** Daily: _____ | Monthly: _____

**Dopad:** Budget tracking v performance monitor, auto-pause při dosažení.

---

#### Q14: Maximum concurrent background tasks/processes?
**Kontext:** Kolik věcí může Sophia dělat najednou.

**Možnosti:**
- **A)** 1 (strict serialization)
- **B)** 3 (light concurrency)
- **C)** 5 (moderate concurrency)
- **D)** 10 (heavy concurrency)
- **E)** Unlimited

**Tvá volba:** _____

**Dopad:** Task queue concurrency limits, resource allocation.

---

#### Q15: Disk space limits?
**Kontext:** Logs, memory DB, state snapshots mohou růst.

**Limits:**
- Logs: _____ GB
- ChromaDB: _____ GB
- State snapshots: _____ GB
- Total project: _____ GB

**Tvá volba:** _____

**Dopad:** Automatic cleanup policies, rotation strategies.

---

### 🛠️ Kategorie 6: Tooling & Integration

#### Q16: Priorita pro advanced tooling implementaci?
**Kontext:** roberts-notes.txt zmiňuje browser control, playwright, computer-use.

**Seřaď podle priority (1 = nejvyšší):**
- [ ] Browser automation (Playwright)
- [ ] Cloud browser (Browserbase/Stagehand)
- [ ] Computer-use (Gemini/Claude desktop control)
- [ ] Jiné: _____________________

**Tvá volba:** 
1. _____
2. _____
3. _____

**Dopad:** Phase 7 implementation order.

---

#### Q17: Jules zůstává primární coding agent?
**Kontext:** Existují alternativy (Copilot Workspace, Cursor, Cline).

**Možnosti:**
- **A)** ✅ ANO - Jules je primární, ostatní jako fallback
- **B)** ❌ NE - Přejít na Copilot Workspace (lepší GitHub integrace)
- **C)** ⚖️ Multi-agent: Sophia si vybírá best tool for job

**Tvá volba:** _____

**Dopad:** Integration architecture, API dependencies.

---

#### Q18: Tests/builds: GitHub Actions vs local execution?
**Kontext:** Kde se mají spouštět testy?

**Možnosti:**
- **A)** GitHub Actions (offload compute, CI/CD standard)
- **B)** Local execution (faster feedback, no queue)
- **C)** Hybrid (local for quick checks, GH Actions for full suite)

**Tvá volba:** _____

**Dopad:** Test execution strategy v process manager.

---

## 🎬 CO SE STANE PO ZODPOVĚZENÍ?

### Okamžitě vytvořím:

1. **Design Specs** (2-3 dny)
   - `docs/en/design/EVENT_SYSTEM.md` - Event bus architecture
   - `docs/en/design/TASK_QUEUE.md` - Task management system
   - `docs/en/design/LOOP_MIGRATION_STRATEGY.md` - Safe refactor guide
   - `docs/en/design/AUTONOMY_GUARDRAILS.md` - Safety boundaries

2. **Phase 1 Implementation Plan** (1 den)
   - `docs/en/roadmap/05_CONTINUOUS_LOOP.md` - Detailed spec
   - Pydantic models for events and tasks
   - Migration checklist
   - Testing strategy

3. **Code Reviews & Updates** (1 den)
   - Update conflicting documentation
   - Fix roadmap statuses
   - Create plugin specs

### Pak můžeme začít implementovat:

**Week 1:** Continuous Loop (event-driven kernel)  
**Week 2:** Process Management + State Persistence  
**Week 3:** Memory Consolidation + Self-Improvement  

---

## 📝 JAK ODPOVĚDĚT?

Můžeš odpovědět dvěma způsoby:

### Možnost A: Rychlá odpověď
```
Q1: A
Q2: B ($1.00)
Q3: A
Q4: C
Q5: Všechny + obsah .env
Q6: C (1 GB)
Q7: A
Q8: A
Q9: A
Q10: A
Q11: Všechny kromě "Vše"
Q12: D
Q13: Daily: B, Monthly: B
Q14: C
Q15: Logs: 1GB, ChromaDB: 1GB, Snapshots: 500MB, Total: 5GB
Q16: 1-Playwright, 2-Browserbase, 3-Computer-use
Q17: A
Q18: C
```

### Možnost B: Detailní diskuse
Můžeme projít každou kategorii a prodiskutovat důsledky jednotlivých rozhodnutí.

---

## ⏰ Timeline Po Obdržení Odpovědí

- **Day 0 (Today):** Questions answered
- **Days 1-3:** Create all design specs
- **Day 4:** Phase 1 implementation plan
- **Days 5-11:** Implement Phase 1 (Continuous Loop)
- **Days 12-14:** Testing & refinement
- **Week 3+:** Phase 2-3 implementation

---

## 🎯 Závěr

Sophia má **excelentní základ** (10/10 architektura, skvělé pluginy).

K plné autonomii chybí **"jen" orchestrace** - continuous loop, task management, memory consolidation.

**Ale potřebuji tvé strategické rozhodnutí**, abych implementoval správným způsobem.

**Tvé odpovědi = green light pro začátek implementace.** 🚀

---

**Ready When You Are!** ✅
