# 🚀 Quick Start Prompt - Sophia Stabilization

**Datum:** 2025-11-04 | **Branch:** `feature/year-2030-ami-complete` | **Status:** Dependency Injection DONE ✅

---

## 📋 TVŮJ ÚKOL

Pokračuj v `docs/STABILIZATION_EXECUTION_PLAN.md` - zbývající úkoly:

1. **Real-World Jules Test** - Ověř delegate_task s API
2. **Integration Tests** - Aktivuj 16 Jules CLI testů  
3. **Code Quality** - black, ruff, mypy pass
4. **Dokumentace** - Update User/Developer Guide

---

## 📚 POVINNÉ ČTENÍ (PŘED ZAČÁTKEM!)

### 1. Operační Manuál ⚡ NEJDŮLEŽITĚJŠÍ
**`docs/cs/AGENTS.md`** nebo **`docs/en/AGENTS.md`**

**Zlacená pravidla:**
1. JÁDRO JE POSVÁTNÉ (core/ jen přes benchmark debugging)
2. VŠE JE PLUGIN (nová funkce = nový soubor v plugins/)
3. KÓD BEZ TESTU NEEXISTUJE (povinné testy)
4. AKTUALIZUJ WORKLOG.MD (po každém kroku)
5. DOKUMENTACE POVINNÁ (EN + CS sync)
6. KÓD JEN ANGLICKY (comments, docstrings, logs)

### 2. Development Guidelines
**`docs/en/04_DEVELOPMENT_GUIDELINES.md`**

- PEP 8, 100% type hints, Google docstrings
- Dependency injection: config přes `setup()`, NIKDY přímo
- Logger: `context.logger`, NIKDY module-level
- Konfigurace: `config.get("all_plugins")`, `config.get("logger")`

### 3. Stabilizační Plán
**`docs/STABILIZATION_EXECUTION_PLAN.md`** - tvůj task list

### 4. Jules Strategy
**`docs/JULES_HYBRID_STRATEGY.md`** - 400+ řádků o hybrid API+CLI

---

## 📊 AKTUÁLNÍ STAV

```
✅ Tests: 177 passed, 16 deselected, 0 failed
✅ Sophia: Odpovídá v <30s
✅ Dependency injection: Všechny pluginy standardizovány
✅ Jules ready: API + CLI + Monitor injected
⏭️  Integration testy čekají na: npm install -g @google/jules
```

---

## 🎯 PRACOVNÍ POSTUP

```bash
# 1. ČTENÍ
cat docs/cs/AGENTS.md
cat docs/STABILIZATION_EXECUTION_PLAN.md
tail -100 WORKLOG.md

# 2. OVĚŘENÍ
pytest tests/ -m "not integration" -v

# 3. PRÁCE
# ... implementace podle plánu ...

# 4. TEST
pytest tests/RELEVANT_TEST.py -v

# 5. WORKLOG
# Aktualizuj WORKLOG.md nahoře (formát v AGENTS.md)

# 6. COMMIT
git add -A
git commit -m "type: description"
```

---

## 📝 WORKLOG FORMÁT

```markdown
---
**Mise:** Název úkolu
**Agent:** Tvoje jméno
**Datum:** 2025-11-04
**Status:** DOKONČENO ✅

**1. Plán:**
*   Krok 1
*   Krok 2

**2. Provedené Akce:**
*   Co jsi udělal
*   Soubory změněny

**3. Výsledek:**
*   Výsledek + test stats
---
```

---

## 🚀 ZAČNI TADY

```
1. ✅ Přečti docs/cs/AGENTS.md
2. ✅ Přečti docs/STABILIZATION_EXECUTION_PLAN.md  
3. ✅ Zkontroluj pytest (177 passed?)
4. 🎯 Začni první zbývající task
```

**Tvá první odpověď:**
```
✅ Read AGENTS.md
✅ Read STABILIZATION_EXECUTION_PLAN.md
✅ Tests: 177 passed

Starting: [Task Name]
Plan: [3-5 steps]
```

---

**Full details:** `docs/NEXT_SESSION_PROMPT.md` (446 lines)

**Remember:** Stabilita > Funkce | English only in code | Tests mandatory | WORKLOG.md required

🚀 **Let's go!**
