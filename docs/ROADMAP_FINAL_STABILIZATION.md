# Finální Stabilizační Roadmapa: Cesta ke 100% Robustnosti

**Autor:** Jules
**Datum:** 2025-09-17

## 1. Kontext a Cíl

Tato roadmapa je finálním plánem pro stabilizaci projektu Sophia. Vznikla jako syntéza mé hloubkové analýzy a doporučení ke dvěma navrhovaným Pull Requestům (`feat/web-file-write-chain` a `phase-4-1-aider-test`).

**Hlavní cíl:** Provést sérii jasně definovaných technických úkolů, které vyřeší všechny identifikované problémy s architekturou, závislostmi a procesy. Po dokončení této roadmapy bude projekt ve 100% stabilním, spolehlivém a předvídatelném stavu, připraveném na přechod k Fázi 4 (plná autonomie).

Tato roadmapa nahrazuje všechny předchozí plány a stává se **primárním technickým úkolem**.

---

## 2. Plán Implementace

Úkoly jsou seřazeny podle logické návaznosti a priority.

### FÁZE 1: Sloučení Změn a Adaptace (Merge & Adapt)

**Cíl:** Integrovat kvalitní, již připravené změny z existujících PR a přizpůsobit zbytek kódu tak, aby byl s nimi kompatibilní.

*   **[ ] Úkol 1.1: Sloučit PR `feat/web-file-write-chain`**
    *   **Akce:** Provést `git merge` větve `feat/web-file-write-chain` do `master`.
    *   **Výsledek:** Orchestrace agentů `Planner -> Engineer` bude funkční ve `web/api.py`.

*   **[ ] Úkol 1.2: Sloučit PR `phase-4-1-aider-test`**
    *   **Akce:** Provést `git merge` větve `phase-4-1-aider-test` do `master`.
    *   **Výsledek:** Nástroje v `tools/file_system.py` budou refaktorované, robustnější a budou používat vlastní výjimky.

*   **[ ] Úkol 1.3: Adaptace agentů na nové nástroje**
    *   **Problém:** Agenti, kteří používají `FileSystemTool`, nyní musí být schopni zpracovat výjimky místo kontroly chybových stringů.
    *   **Zadání:** Upravit kód v `agents/engineer_agent.py` a dalších relevantních agentech. Místo kontroly `if "Error:" in result:` implementovat `try...except FileSystemError:` bloky pro robustní ošetření chyb.
    *   **Akceptační kritérium:** Agenti správně reagují na výjimky vyhozené z nástrojů.

---

### FÁZE 2: Sjednocení a Zpevnění Architektury (Unify & Harden)

**Cíl:** Odstranit architektonické nekonzistence a vyřešit problémy s testovacím prostředím.

*   **[ ] Úkol 2.1: Sjednocení orchestrace agentů**
    *   **Problém:** Po Fázi 1 bude správná logika orchestrace v `web/api.py`, ale stále chybná v `main.py`.
    *   **Zadání:**
        1.  Vytvořit nový modul, např. `core/orchestrator.py`.
        2.  Přesunout logiku řetězení agentů (`Planner -> Engineer -> Tester`) z `web/api.py` do tohoto nového modulu.
        3.  Refaktorovat `web/api.py` i `main.py` tak, aby oba pouze volaly tento centrální orchestrátor.
    *   **Akceptační kritérium:** Existuje jediný zdroj pravdy pro logiku spolupráce agentů, čímž je odstraněna architektonická divergence.

*   **[ ] Úkol 2.2: Oprava nestability testovacího prostředí**
    *   **Problém:** `uvicorn` server nerespektuje spolehlivě proměnnou prostředí `SOPHIA_ENV=test`, což brání spolehlivému testování webového API.
    *   **Zadání:** Prozkoumat a implementovat robustnější způsob konfigurace `uvicorn`. Pravděpodobným řešením je vytvoření spouštěcího skriptu (např. `run_web_server.py`), který bude programově načítat konfiguraci a spouštět `uvicorn.run()` s explicitně nastavenými parametry, místo spoléhání na CLI a proměnné prostředí.
    *   **Akceptační kritérium:** Webový server lze spolehlivě spustit v produkčním i testovacím režimu a testovací režim vždy správně aplikuje mockování.

---

### FÁZE 3: Opevnění Procesů (Process Fortification)

**Cíl:** Zavést nástroje a procesy, které dlouhodobě zajistí stabilitu a kvalitu projektu.

*   **[ ] Úkol 3.1: Správa závislostí pomocí `pip-tools`**
    *   **Problém:** `requirements.txt` byl v minulosti zdrojem konfliktů.
    *   **Zadání:** Zavést `pip-tools` pro systematickou a reprodukovatelnou správu závislostí (vytvořit `requirements.in`, generovat `requirements.txt`).
    *   **Akceptační kritérium:** Prostředí je 100% reprodukovatelné.

*   **[ ] Úkol 3.2: Automatizace kontroly kvality (Pre-commit Hook)**
    *   **Problém:** Dodržování pravidel z `CODE_OF_CONDUCT.md` je manuální.
    *   **Zadání:** Zavést `pre-commit` hooky pro automatické formátování, lintování a spuštění revizního skriptu.
    *   **Akceptační kritérium:** `git commit` automaticky selže, pokud kód nevyhovuje standardům.

*   **[ ] Úkol 3.3: Sjednocení dokumentace**
    *   **Problém:** Duplicita mezi `AGENTS.md` a `CODE_OF_CONDUCT.md`.
    *   **Zadání:** Sjednotit obsah do `AGENTS.md` a smazat `CODE_OF_CONDUCT.md`.
    *   **Akceptační kritérium:** Existuje pouze jeden centrální dokument s pravidly.
