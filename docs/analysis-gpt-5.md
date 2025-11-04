# 🔍 SOPHIA PROJECT ANALYSIS
**Analyst:** GPT-5
**Date:** November 4, 2025

## 📊 EXECUTIVE SUMMARY
Sophia má solidní Core‑Plugin architekturu a po Phasích 1–3 stojí na dobrém základě, ale poslední úpravy zavedly regresi v testech a zásadní provozní problém: single‑run vstup nevede k odpovědi (timeout). Krátký běh spouští WebUI server, tiskne dvojitý boot banner a do 15 s nevrátí odpověď. Testy aktuálně: 12 failed, 2 errors, 179 passed. Stabilizace (TIER 1) je realisticky otázkou hodin; po ní může plynule začít Phase 4 (autonomní operace).

## ⭐ RATINGS (1-10)
- Architecture Quality: 8/10
- Code Quality: 7/10
- Test Coverage: 7/10
- Production Readiness: 5/10
- **Overall Health: 6.5/10**

## 🚨 CRITICAL ISSUES (Priority Order)

### Issue 1: Neodpovídá na vstup (timeout v run.py)
- **Severity:** CRITICAL
- **Impact:** CLI/skriptové ověření nefunguje; blokuje akceptaci i demo
- **Root Cause:** V single‑run scénáři se spustí WebUI (Uvicorn) a interaktivní rozhraní; jednorázový dotaz se nezpracuje v deadline (15 s). V legacy části mohou interface pluginy navíc blokovat čtením vstupu a duplikovat boot sekvenci.
- **Fix Effort:** 1–2 hod
- **Fix Strategy:**
  1) Přidat explicitní once‑mode (např. `--once "text"`) v `run.py`, který přeskočí WebUI a přímo zavolá event‑driven smyčku s `single_run_input`.
  2) V `core/kernel.py` při `single_run_input` nespouštět interaktivní `interface_*` (jen registrace callbacků bez blokování) a garantovat odpověď do 5 s.
  3) Logovat jasnou větu „Single‑run mode (no WebUI)“ a ukončit proces po odpovědi.

### Issue 2: Jules CLI – „coroutine was never awaited“ (10 testů)
- **Severity:** HIGH
- **Impact:** 10 selhání testů; riziko nespolehlivosti a leaků
- **Root Cause:** Metody pluginu jsou `async`, ale testy/callsites je neawaitují; navíc schema `get_tool_definitions()` očekává názvy bez prefixu.
- **Fix Effort:** 1–2 hod
- **Fix Strategy:**
  1) Sjednotit kontrakt: buď přepnout veřejné metody na synchronní (I/O přes `subprocess.run`), nebo ponechat `async` a důsledně je `await`‑ovat v testech i Kernelu.
  2) Urovnat schema: `function.name` bez `tool_jules_cli.` prefixu, sjednotit s ostatními tooly.
  3) Dodat adapter v Kernelu (pokud mix sync/async), aby volání byla konzistentní.

### Issue 3: Sleep Scheduler – chybějící guardy (2 errors)
- **Severity:** HIGH
- **Impact:** Nestabilita fáze 3 v testech
- **Root Cause:** Scheduler běží bez plného DI (`consolidator`, `event_bus`) a nemá no‑op guardy.
- **Fix Effort:** 0.5–1 hod
- **Fix Strategy:** V `core_sleep_scheduler.py` přidat guardy (pokud chybí consolidator, jen warning); v testech zajistit jednoduchý fake event bus a korektní lifecycle `start()/stop()`.

### Issue 4: Logging config test selhává
- **Severity:** MEDIUM
- **Impact:** Neidempotentní setup zvyšuje šum a flaky chování
- **Root Cause:** `setup_logging()` přidává handlery/filtry opakovaně; pořadí a SessionIdFilter nejsou stabilní.
- **Fix Effort:** 0.5–1 hod
- **Fix Strategy:** Udělat `setup_logging()` idempotentní (nejdřív odebrat existující handlery, pak přidat očekávané; zajistit jednotné přidání `SessionIdFilter`).

### Issue 5: Volitelné závislosti blokují čistý start
- **Severity:** MEDIUM
- **Impact:** `tool_web_search` padá na `googleapiclient` při importu
- **Root Cause:** Tvrdý import volitelné dependency
- **Fix Effort:** 0.5 hod
- **Fix Strategy:** Obalit import do `try/except`, `self.enabled=False`, varování do logu; případně označit jako optional dep v requirements.

## 📋 PRIORITIZED ACTION PLAN

### 🔴 TIER 1: BLOCKERS (Must Fix Now)
1. Single‑run režim a garantovaná odpověď do 5 s – 2 h – odblokuje CLI a akceptační tok
2. Jules CLI kontrakt (sync/async + schema) – 2 h – 10 selhání testů, klíčová integrace
3. Sleep Scheduler guardy – 1 h – stabilita Phase 3 testů
4. Logging idempotence – 1 h – čisté logy a stabilní test
**Total: ~6 hod**

### 🟡 TIER 2: HIGH PRIORITY (Phase 4)
1. Autonomní čtečka `roberts-notes.txt` → generátor úkolů – 4–6 h – start Phase 4
2. Cost/Token tracker do status baru – 4–6 h – viditelnost nákladů a limitů
3. Jules hybrid E2E (API monitor + CLI pull --apply) – 4 h – plná autonomie
**Total: ~12–16 hod**

### 🟢 TIER 3: NICE TO HAVE
1. Soft optional deps (web search) – 0.5 h – čistý boot
2. Idempotentní UI bannery – 0.5 h – UX polish
3. WebUI start pouze na explicitní flag – 1 h – srozumitelné režimy běhu
**Total: ~2 hod**

## 🚀 PHASE 4 RECOMMENDATION

**Build first:** Autonomous Task Runner z `roberts-notes.txt`
**Why:** Přináší okamžitou hodnotu – Sophia sama vybírá úkoly, plánuje kroky a deleguje na Jules; lze snadno omezovat rozpočtem a guardraily.
**Effort:** 1–2 dny (MVP: watcher + planner + Jules monitor + pull/apply přes CLI)
**Risks:** Škálování úkolů, prevence smyček, kontrola nákladů – mitigovat přes `autonomy.yaml`, guardraily v Kernelu a monitor.

## 💡 CONTROVERSIAL OPINIONS
- Pozastavit UI polishing, dokud nejsou testy zelené a single‑run odpověď do 5 s.
- Unifikovat kontrakt toolů: buď všude synchronní metody (I/O), nebo všude `async` + důsledné `await`.
- WebUI nespouštět implicitně v single‑run – jen na explicitní flag.
- Minimalizovat zásahy do `core/` – preferovat řešení v pluginech; core jen pro architektonické uzly (Phase 1–3, DI, eventy, idempotence setupu).

## 🧠 GPT‑5: unikátní doporučení a „edge“

- Deterministický „PlanSim“ před exekucí: lehká statická simulace plánu (regex na `${step_N.field}`, kontrola schema required/optional, side‑effect lint) – vrátit zpět do planneru opravný nápovědný diff bez volání LLM (šetří tokeny i čas).
- JSON‑Mode „strict repair“: generovat opravné prompty s vloženým `model_json_schema()` konkrétní funkce + ukázkou minimal diffu; GPT‑5 zvládá přesné JSONy – výrazně snižuje počet re‑try.
- Paralelní hypotézy plánů (k‑best): Pro kritické úlohy vygenerovat 2–3 levné varianty plánu (levný model) a vybrat nejlepší podle deterministických metrik (počet kroků, riziko I/O, potřeba práv) – před odesláním na dražší inference.
- Heuristiky pro Jules hybrid: pokud `get_session()` hlásí COMPLETED, ale chybí výsledky, automaticky přepnout na `jules remote pull --apply` a logovat diffs; GPT‑5 může shrnout diffs do lidsky čitelné rekapitulace v odpovědi.
- Token‑aware summarizace: průběžné micro‑shrnutí stavů (router → planner → executor) s horní hranicí tokenů per fáze; GPT‑5 zvládá vysokou kompresi bez ztráty klíčových technických detailů.

## 🎯 SUCCESS PROBABILITY: 92%

**Confidence factors:**
- ✅ Silná architektura (Phase 1–3, testy, dokumentace)
- ⚠️ Regrese jsou lokální a rychle opravitelné (Jules CLI, logging, sleep)
- ❌ Runtime UX blokuje akceptaci – nutné rychle opravit single‑run a režimy běhu

## ✅ Quality gates (aktuální běh)
- Build/Run: PASS (start proběhne, ale končí timeoutem v single‑run scénáři)
- Lint/Typecheck: N/A (nebylo spuštěno v této analýze)
- Tests: FAIL (12 failed, 2 errors, 179 passed)

## 📎 Poznámky k verifikaci
- Testy: `pytest tests/ -v --tb=short` → 12 failed, 2 errors, 179 passed
- Běh: `timeout 15 python run.py "test"` → spouští WebUI, dvojitý banner, timeout (143)

---

Po schválení mohu rovnou začít s TIER 1 opravami (single‑run režim, Jules CLI kontrakt, guardy ve sleep scheduleru, idempotentní logging) a doplnit malý E2E test „single‑run odpovědi do 5 s“, aby se problém už nevrátil.
