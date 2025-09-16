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

- [x] **9.1. Upgrade Databáze:**
    -   Nahradit stávající řešení s SQLite za client-server databázi PostgreSQL.
    -   Upravit `memory/episodic_memory.py` a `web/api.py` pro práci s novou databází.
    -   Aktualizovat `requirements.txt` o `psycopg2-binary` nebo podobný driver.
    -   Aktualizovat `INSTALL.md` a `setup.sh` s instrukcemi pro spuštění PostgreSQL (např. pomocí Dockeru).

- [x] **9.2. Inteligentní Guardian:**
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
    -   Refaktorovat MemoryReaderTool a všechny paměťové nástroje na univerzální async/sync rozhraní (hotovo, viz WORKLOG.md 2025-09-14 22:30).

- [x] **10.2. Nástroje pro Tvorbu:**
    -   Vytvořit `tools/file_system.py` s nástroji pro čtení, zápis, a výpis souborů v `/sandbox` (hotovo, univerzální async/sync rozhraní).
    -   Vytvořit `tools/code_executor.py` s nástroji pro spouštění Python skriptů a `unittest` testů v `/sandbox` a zachytávání jejich výstupu a chyb (hotovo, univerzální async/sync rozhraní).
    -   Všechny nástroje nyní podporují bezpečné použití v CrewAI (sync) i AutoGen (async) workflow.

### Fáze 11: Zrození Týmu Tvůrců

**Cíl:** Vylepšit etické jádro a implementovat agenty schopné psát a testovat kód.

- [x] **11.1. Konstituční AI:**
    -   Prozkoumat a integrovat knihovnu `LangGraph`.
    -   Přepracovat `core/ethos_module.py`, aby používal cyklický proces (kritika -> revize) inspirovaný Konstituční AI, místo jednoduchého porovnání.

- [x] **11.2. Oživení Agentů (CrewAI):**
    -   Plně implementovat `agents/engineer_agent.py` a vybavit ho nástroji pro práci se soubory a spouštění kódu.
    -   Plně implementovat `agents/tester_agent.py` a vybavit ho stejnými nástroji.

### Fáze 12: Probuzení Kreativity

**Cíl:** Uzavřít smyčku autonomní tvorby a rozšířit schopnosti o kreativní procesy.

- [x] **12.1. Tým Snů (AutoGen):**
    -   Prozkoumat a integrovat framework `AutoGen`.
    -   Vytvořit specializovaný tým agentů (`Philosopher`, `Architect`) v `AutoGen`, který bude aktivován během "spánkové" fáze pro generování nových nápadů a strategií.

- [x] **12.2. Uzavření Smyčky Tvorby:**
    -   Upravit `core/consciousness_loop.py` tak, aby dokázal orchestrovat celý řetězec: `Planner` -> `Engineer` -> `Tester`.
    -   Implementovat logiku pro zpracování zpětné vazby (např. když testy selžou, úkol se vrátí Inženýrovi s chybovou hláškou).

---

### Fáze 13: Integrace Aider IDE Agenta


**Cíl:** Využít Aider IDE jako autonomní evoluční motor – agent, který umožní Sophii samostatně navrhovat, upravovat a refaktorovat vlastní kód v sandboxu, a tím realizovat skutečnou autonomní evoluci schopností.

- [x] **13.1. Analýza a příprava integrace:**
    -   Prozkoumat možnosti Aider IDE (https://github.com/paul-gauthier/aider) a jeho CLI/API.
    -   Navrhnout Aider IDE jako samostatného autonomního agenta s právem měnit kód Sophie v sandboxu.
- [x] **13.2. Implementace AiderAgent:**
    -   Vytvořit wrapper třídu `AiderAgent` v `agents/aider_agent.py` pro komunikaci s Aider IDE přes CLI.
    -   Definovat protokol pro předávání úkolů (např. JSON přes stdin/stdout nebo REST endpoint).
    -   Omezit všechny operace na `/sandbox` a validovat výstup před commitem.
    -   Zajistit, že všechny změny budou auditovatelné (git log, review) a podléhají etické kontrole (Ethos module, případně schválení jiným agentem).
- [x] **13.3. Evoluční workflow:**
    -   Umožnit Aider agentovi samostatně navrhovat a realizovat změny kódu na základě cílů nebo vlastního rozhodnutí v rámci evoluční smyčky.
    -   Ostatní agenti (Planner, Philosopher, Architect) navrhují cíle, hodnotí změny a poskytují zpětnou vazbu, ale Aider agent provádí úpravy.
    -   Všechny změny musí být bezpečné, auditované a revertovatelné.
    -   Odstranit zbytečnou delegaci a složitou mezivrstvu – Aider agent je hlavní motor evoluce.
    -   Pravidelně revidovat, zda některé mechanismy nejsou redundantní nebo překonané a roadmapu dále zjednodušovat.

### Fáze 14: Robustní LLM integrace (GeminiLLMAdapter)

**Cíl:** Zajistit robustní, snadno vyměnitelnou a testovatelnou integraci LLM pro všechny agenty.

- [x] **14.1. Návrh a implementace GeminiLLMAdapter:**
    -   Navrhnout a implementovat vlastní adapter pro Google Gemini API (`core/gemini_llm_adapter.py`).
    -   Zajistit kompatibilitu s CrewAI a orchestrace agentů (předávání `llm=llm`).
    -   Připravit možnost snadného přepnutí na LangChain wrapper v budoucnu.
    -   Implementovat sledování spotřeby tokenů a základní testy.
    -   Aktualizovat dokumentaci (`README.md`, `INSTALL.md`, `ARCHITECTURE.md`, `CONCEPTS.md`).
    -   Ověřit, že všichni agenti používají nový adapter a vše je plně funkční.
    -   Přidat závislost `google-generativeai` do requirements.txt.
    -   Otestovat inicializaci a základní workflow agentů s novým adapterem.
    -   Zapsat změny do WORKLOG.md a roadmapy.