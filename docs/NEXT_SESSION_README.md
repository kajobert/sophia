# 📚 Next Session Documentation

Tato dokumentace poskytuje kompletní kontext pro pokračování práce na projektu Sophia.

## 🎯 Pro Nový Chat / Nového AI Agenta

### Rychlý Start (Doporučeno)

**Zkopíruj obsah tohoto souboru do nového chatu:**
```
docs/COPY_PASTE_PROMPT.txt
```

Ten tě nasměruje na:

### Úplný Kontext (446 řádků)
```
docs/NEXT_SESSION_PROMPT.md
```

**Obsahuje:**
- ✅ Kompletní přehled mise a hotových úkolů
- 📚 Povinné čtení (AGENTS.md, Development Guidelines, atd.)
- 🏗️ Architektura a konfigurace projektu
- 📖 Jules Hybrid Strategy shrnutí
- 📝 WORKLOG formát a požadavky
- 🎯 Kritéria úspěchu
- 🔧 Vývojové nástroje a příkazy

### Rychlá Verze (100 řádků)
```
docs/NEXT_SESSION_QUICK.md
```

**Obsahuje:**
- Zkrácený task list
- Nejdůležitější odkazy
- Základní workflow
- Current status

## 📋 Hierarchie Dokumentace

### Úroveň 1: Operační Manuál (MUSÍŠ ČÍST)
```
docs/cs/AGENTS.md  (Czech)
docs/en/AGENTS.md  (English)
```
- **Nejvyšší zákon** - 5 zlatých pravidel
- Operační postup (7 kroků)
- WORKLOG formát
- Benchmark debugging princip

### Úroveň 2: Technické Standardy
```
docs/en/04_DEVELOPMENT_GUIDELINES.md
```
- Coding style (PEP 8, type hints, docstrings)
- Dependency injection pattern
- Configuration management
- Context-aware logging

### Úroveň 3: Architektura
```
docs/en/03_TECHNICAL_ARCHITECTURE.md
```
- Core-Plugin model
- PluginTypes a BasePlugin
- SharedContext flow
- EventBus + TaskQueue

### Úroveň 4: Aktuální Plán
```
docs/STABILIZATION_EXECUTION_PLAN.md
```
- Task 1-4 breakdown
- Časové odhady
- Success criteria

### Úroveň 5: Specifické Strategie
```
docs/JULES_HYBRID_STRATEGY.md
```
- API + CLI hybrid architecture
- Persistent workers koncept
- Scaling strategy (1 → 100 workers)
- Tool usage examples

## 📊 Aktuální Stav (2025-11-04)

### ✅ Dokončeno
- Dependency injection standardizace (8 plugins)
- Input responsiveness (--once mode)
- Jules CLI re-enabled (hybrid strategy)
- Logging idempotence
- Sleep scheduler guardrails

### 🎯 Zbývá
- Real-world Jules validation
- Integration tests (16 skipped)
- Code quality pass (black, ruff, mypy)
- Documentation updates (User/Dev Guide)

### 📈 Metriky
```
Tests: 177 passed, 16 deselected, 0 failed
Sophia: <30s response time
Code: 100% English, type-annotated
Commits: 4 (dependency injection + docs)
```

## 🔄 Workflow pro Nový Chat

1. **Zkopíruj** `COPY_PASTE_PROMPT.txt` do nového chatu
2. **Počkej** až agent potvrdí, že četl AGENTS.md
3. **Sleduj** jak agent postupuje podle 7-step workflow
4. **Ověřuj** že aktualizuje WORKLOG.md po každém kroku
5. **Kontroluj** že všechny testy procházejí před commitem

## 🚨 Red Flags

Pokud agent:
- ❌ Neaktualizuje WORKLOG.md → STOP, připomeň pravidlo
- ❌ Píše česky v kódu → STOP, pouze angličtina
- ❌ Mění core/ bez zdůvodnění → STOP, benchmark debugging
- ❌ Commituje bez testů → STOP, testy povinné
- ❌ Nečetl AGENTS.md → STOP, povinné čtení

## 📞 Kontakt / Eskalace

Pokud agent:
- Narazí na neřešitelný problém → Zapíše do WORKLOG s STATUS: SELHALO
- Potřebuje rozhodnutí → Označí jako "VYŽADUJE POMOC"
- Najde architektonický problém → Benchmark debugging proces

## 📚 Další Zdroje

```
WORKLOG.md           - Kompletní historie vývoje (2200+ řádků)
README.md            - Přehled projektu
docs/STATUS_REPORT_2025-11-04.md - Detailní status
docs/analysis-*.md   - Multi-model analýzy
```

---

**Vytvořeno:** 2025-11-04  
**Agent:** GitHub Copilot  
**Účel:** Zajistit kontinuitu práce mezi chat sessions  
**Verze:** 1.0  

Užij si práci s Sophií! 🚀
