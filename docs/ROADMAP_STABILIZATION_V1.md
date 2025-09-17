# Roadmapa Stabilizace v1.0: Cesta ke 100% Robustnosti

**Autor:** Jules
**Datum:** 2025-09-17

## 1. Kontext a Cíl

Tato roadmapa byla vytvořena na základě hloubkové analýzy `WORKLOG.md` a kódu projektu. Analýza odhalila systematické problémy v oblasti správy závislostí, nestability integrační vrstvy (především `crewai`) a nedokončeného architektonického dluhu.

**Hlavní cíl této roadmapy je jediný: Dosáhnout 100% stability, spolehlivosti a předvídatelnosti chování projektu Sophia, aby bylo možné bezpečně přejít k Fázi 4 (plná autonomie).**

Tato roadmapa nahrazuje předchozí plány a stává se **primárním technickým úkolem**.

---

## 2. Plán Implementace

Úkoly jsou seřazeny podle nejvyšší priority. Každá fáze musí být dokončena, než se přejde k další.

### FÁZE 1: Oprava Jádra Architektury (Core Architecture Repair)

**Cíl:** Opravit kritické chyby v implementaci a zajistit, aby kód odpovídal navržené architektuře.

*   **[ ] Úkol 1.1: Refaktoring a oprava orchestrace v `main.py`**
    *   **Problém:** Hlavní smyčka nepoužívá `SharedContext` a nevolá správně metody `run_task` jednotlivých agentů.
    *   **Zadání:**
        1.  Kompletně přepsat logiku zpracování úkolu v `main.py`.
        2.  Implementovat správné řetězení agentů (`Planner` -> `Engineer` -> `Tester`) s využitím `SharedContext` pro předávání dat.
        3.  Vytvářet **instance** agentů (`planner = PlannerAgent(llm)`) a volat jejich metody `run_task(context)`.
        4.  Zajistit, aby blokující volání `crew.kickoff()` uvnitř metod `run_task` byla spouštěna v `asyncio` kompatibilním režimu (např. `await loop.run_in_executor(None, ...)`), aby neblokovala hlavní `async` smyčku.
    *   **Akceptační kritérium:** Plný cyklus od naplánování po otestování kódu proběhne úspěšně s využitím `SharedContext` a bude viditelný v logu.

*   **[ ] Úkol 1.2: Implementace cyklu opravy (Retry Loop)**
    *   **Problém:** Selhání testů vede k okamžitému selhání celého úkolu.
    *   **Zadání:**
        1.  Do hlavní smyčky v `main.py` implementovat `for` cyklus (např. pro 3 pokusy).
        2.  Pokud `TesterAgent` vrátí neúspěch, výsledek testů se zapíše do `SharedContext` a ten je vrácen zpět `EngineerAgentovi` pro další iteraci.
        3.  Teprve po vyčerpání pokusů je úkol označen jako finálně neúspěšný.
    *   **Akceptační kritérium:** Testovací scénář se selháním testu prokazatelně spustí cyklus opravy.

---

### FÁZE 2: Zpevnění Integrační Vrstvy (Integration Layer Hardening)

**Cíl:** Minimalizovat rizika plynoucí z nepředvídatelného chování externích frameworků.

*   **[ ] Úkol 2.1: Sjednocení a zjednodušení mockování**
    *   **Problém:** Mockování je implementováno na více místech a různými způsoby (`conftest.py`, `web/api.py`, `core/mocks.py`), což může vést k nekonzistencím.
    *   **Zadání:**
        1.  Sjednotit veškerou mockovací logiku do `core/mocks.py`.
        2.  `tests/conftest.py` a `web/api.py` by měly pouze volat centrální mockovací handlery z `core/mocks.py`, nikoli obsahovat vlastní logiku.
        3.  Ověřit, že mockování `litellm.completion` je dostatečně robustní a pokrývá všechny případy (včetně `acompletion`).
    *   **Akceptační kritérium:** Testy i webové API v testovacím režimu fungují a spoléhají na jediný zdroj pravdy pro mockování.

*   **[ ] Úkol 2.2: Izolace od `crewai` a `langchain`**
    *   **Problém:** Projekt je zranitelný vůči "breaking changes" v `crewai` a `langchain`.
    *   **Zadání:**
        1.  Vytvořit "anti-korupční vrstvu" (wrapper třídy) kolem klíčových objektů `crewai` (`Agent`, `Task`, `Crew`).
        2.  Vlastní kód Sophie (`main.py`, agent wrappery) by měl komunikovat primárně s touto naší vrstvou, nikoli přímo s `crewai` objekty.
        3.  Tato vrstva bude zodpovědná za překlad mezi `SharedContext` a tím, co očekává `crewai`, a za ošetření chyb specifických pro `crewai`.
    *   **Akceptační kritérium:** Budoucí změna v `crewai` (např. přejmenování parametru v `Task`) bude vyžadovat úpravu pouze v naší izolační vrstvě, nikoli na mnoha místech v aplikaci.

---

### FÁZE 3: Opevnění Procesů a Závislostí (Process & Dependency Fortification)

**Cíl:** Zavést procesy a nástroje, které dlouhodobě zajistí stabilitu a kvalitu.

*   **[ ] Úkol 3.1: Správa závislostí pomocí `pip-tools`**
    *   **Problém:** `requirements.txt` byl v minulosti zdrojem konfliktů.
    *   **Zadání:**
        1.  Vytvořit soubor `requirements.in`, který bude obsahovat pouze přímé, top-level závislosti projektu (např. `crewai`, `fastapi`, `psutil`).
        2.  Nainstalovat `pip-tools` (`pip install pip-tools`).
        3.  Vygenerovat plně pinovaný, konzistentní `requirements.txt` pomocí příkazu `pip-compile requirements.in`.
        4.  Aktualizovat `INSTALL.md` a `README.md` o nový postup správy závislostí.
    *   **Akceptační kritérium:** Prostředí je 100% reprodukovatelné a správa závislostí je systematická.

*   **[ ] Úkol 3.2: Automatizace kontroly kvality (Pre-commit Hook)**
    *   **Problém:** Dodržování pravidel z `CODE_OF_CONDUCT.md` je manuální.
    *   **Zadání:**
        1.  Nainstalovat a nakonfigurovat `pre-commit` (`pip install pre-commit`).
        2.  Vytvořit konfigurační soubor `.pre-commit-config.yaml`.
        3.  Nastavit hooky pro automatické formátování (`black`), lintování (`ruff` nebo `flake8`) a spuštění revizního skriptu `run_review.py`.
    *   **Akceptační kritérium:** Příkaz `git commit` automaticky selže, pokud kód nevyhovuje definovaným standardům kvality.

*   **[ ] Úkol 3.3: Sjednocení dokumentace**
    *   **Problém:** Duplicita mezi `AGENTS.md` a `CODE_OF_CONDUCT.md`.
    *   **Zadání:**
        1.  Přesunout veškerý relevantní obsah z `CODE_OF_CONDUCT.md` do `AGENTS.md`.
        2.  Smazat soubor `CODE_OF_CONDUCT.md`.
    *   **Akceptační kritérium:** Existuje pouze jeden centrální dokument s pravidly pro agenty.
