# Projekt Sophia V4: Roadmapa k Autonomnímu Tvůrci

Tento dokument slouží jako hlavní plán a TODO list pro vývoj AGI Sophia V4. Cílem této etapy je přeměnit Sophii z myslitele na autonomního tvůrce, který dokáže samostatně psát, testovat a vylepšovat kód v bezpečném prostředí.

## CÍLOVÝ STAV: Sophia V4 - Autonomní Tvůrce

Cílem je vytvořit systém, který:
-   Disponuje robustní infrastrukturou (PostgreSQL, proaktivní monitoring).
-   Využívá pokročilé open-source nástroje pro paměť a etiku.
-   Pro exekutivní úkoly používá disciplinovaný tým agentů (CrewAI).
-   Pro kreativní a sebereflexivní procesy využívá flexibilní tým agentů (AutoGen).
-   Dokáže v sandboxu samostatně naplánovat, napsat a otestovat funkční kód.

---

## Roadmapa Implementace V4

### Fáze 9: Evoluce Infrastruktury

**Cíl:** Připravit robustní, škálovatelné a bezpečné prostředí pro autonomní operace.

- [ ] **9.1. Upgrade Databáze:**
    -   Nahradit stávající řešení s SQLite za client-server databázi PostgreSQL.
    -   Upravit `memory/episodic_memory.py` a `web/api.py` pro práci s novou databází.
    -   Aktualizovat `requirements.txt` o `psycopg2-binary` nebo podobný driver.
    -   Aktualizovat `INSTALL.md` a `setup.sh` s instrukcemi pro spuštění PostgreSQL (např. pomocí Dockeru).

- [ ] **9.2. Inteligentní Guardian:**
    -   Integrovat knihovnu `psutil` do `guardian.py`.
    -   Rozšířit monitorovací smyčku o kontrolu systémových prostředků (využití CPU a RAM).
    -   Implementovat logiku, která v případě překročení prahových hodnot (např. 90% RAM) provede "měkký" restart nebo pošle varování.

- [x] **9.3. Vytvoření Sandboxu:**
    -   Vytvořit a zabezpečit adresář `/sandbox`.
    -   Zajistit, aby kód spuštěný v sandboxu neměl přístup k souborům mimo tento adresář.

### Fáze 10: Vybavení Dílny

**Cíl:** Vytvořit a integrovat pokročilé nástroje, které agentům umožní efektivně pracovat.

- [x] **10.1. Implementace Pokročilé Paměti:**
    -   Prozkoumat a integrovat externí paměťovou knihovnu (např. `GibsonAI/memori`).
    -   Nahradit naši stávající jednoduchou logiku pro "váhu" a "blednutí" za robustnější řešení z této knihovny.

- [x] **10.2. Nástroje pro Tvorbu:**
    -   Vytvořit `tools/file_system_tool.py` s nástroji pro čtení, zápis, a výpis souborů v `/sandbox`.
    -   Vytvořit `tools/code_executor_tool.py` s nástroji pro spouštění Python skriptů a `unittest` testů v `/sandbox` a zachytávání jejich výstupu a chyb.

### Fáze 11: Zrození Týmu Tvůrců

**Cíl:** Vylepšit etické jádro a implementovat agenty schopné psát a testovat kód.

- [ ] **11.1. Konstituční AI:**
    -   Prozkoumat a integrovat knihovnu `LangGraph`.
    -   Přepracovat `core/ethos_module.py`, aby používal cyklický proces (kritika -> revize) inspirovaný Konstituční AI, místo jednoduchého porovnání.

- [ ] **11.2. Oživení Agentů (CrewAI):**
    -   Plně implementovat `agents/engineer_agent.py` a vybavit ho nástroji pro práci se soubory a spouštění kódu.
    -   Plně implementovat `agents/tester_agent.py` a vybavit ho stejnými nástroji.

### Fáze 12: Probuzení Kreativity

**Cíl:** Uzavřít smyčku autonomní tvorby a rozšířit schopnosti o kreativní procesy.

- [ ] **12.1. Tým Snů (AutoGen):**
    -   Prozkoumat a integrovat framework `AutoGen`.
    -   Vytvořit specializovaný tým agentů (`Philosopher`, `Architect`) v `AutoGen`, který bude aktivován během "spánkové" fáze pro generování nových nápadů a strategií.

- [ ] **12.2. Uzavření Smyčky Tvorby:**
    -   Upravit `core/consciousness_loop.py` tak, aby dokázal orchestrovat celý řetězec: `Planner` -> `Engineer` -> `Tester`.
    -   Implementovat logiku pro zpracování zpětné vazby (např. když testy selžou, úkol se vrátí Inženýrovi s chybovou hláškou).