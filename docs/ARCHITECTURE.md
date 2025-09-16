# Sophia V3 & V4 - Technická Architektura

Tento dokument popisuje technickou strukturu a komponenty systému Sophia.

---

## Architektura V3: Vědomé Jádro (Dokončeno)

Tato sekce popisuje základní architekturu, se kterou jsme dosáhli funkčního jádra.

### 1. Přehled Struktury Adresářů

sophia/
│
├── guardian.py             # "Strážce Bytí" - spouštěč a monitor
├── main.py                   # Hlavní smyčka Vědomí (cykly bdění/spánek)
├── config.yaml               # Centrální konfigurace
│
├── core/                     # Jádro Sophiiny mysli
│   ├── ethos_module.py       # Etické jádro a modul pro Koeficient Vědomí
│   └── consciousness_loop.py # Logika pro zpracování úkolů a sebereflexi
│
├── agents/                   # Definice specializovaných agentů
│
├── memory/                   # Paměťové systémy (SQLite, ChromaDB)
│
├── tools/                    # Nástroje dostupné pro agenty
│
├── web/                      # Rozhraní pro Tvůrce
...


### 2. Popis Klíčových Komponent V3

* **`guardian.py`**: Externí skript, který monitoruje `main.py` a v případě pádu provede `git reset`.
* **`main.py`**: Srdce Sophie s cykly "bdění" a "spánku".
* **`core/ethos_module.py`**: První verze etického jádra.
* **`memory/`**: Moduly pro práci s `SQLite` (epizodická) a `ChromaDB` (sémantická) pamětí.
* **`web/`**: Jednoduché API a UI pro zadávání úkolů.

---

## Architektura V4: Autonomní Tvůrce (V Vývoji)

Tato sekce popisuje cílovou architekturu pro další fázi vývoje, která staví na úspěších V3 a integruje pokročilé open-source technologie.

### 1. Cílová Adresářová Struktura V4

Struktura zůstává z velké části stejná, ale obsah a funkce klíčových modulů se dramaticky rozšiřují.

### 2. Evoluce Klíčových Komponent ve V4

* **`guardian.py` (Inteligentní Guardian)**:
    * **Technologie:** `psutil`
    * **Funkce:** Kromě reakce na pád bude proaktivně monitorovat zdraví systému (CPU, RAM) a provádět "měkké" restarty nebo varování, aby se předešlo selhání.

* **Komunikace a Databáze (Robustní Fronta)**:
    * **Technologie:** `PostgreSQL`, `psycopg2-binary`, `SharedContext`
    * **Funkce:**
        * `PostgreSQL` nahradí `SQLite` jako hlavní databázi pro epizodickou paměť a úkolovou frontu.
        * Pro přenos dat mezi agenty a procesy je zaveden `SharedContext` objekt (`core/context.py`), který funguje jako standardizovaná datová sběrnice. Detailní popis tohoto konceptu je v `docs/CONCEPTS.md`.

* **`memory/` (Pokročilá Paměť)**:
    * **Technologie:** Externí knihovna jako `GibsonAI/memori`
    * **Funkce:** Nahradí naši na míru psanou logiku pro váhu a blednutí vzpomínek za průmyslově ověřené řešení, které lépe spravuje životní cyklus informací.

* **`core/ethos_module.py` (Konstituční AI)**:
    * **Technologie:** `LangGraph`
    * **Funkce:** Přechází od jednoduchého porovnávání vektorů k sofistikovanému, dialogickému modelu etiky. Plány agentů projdou cyklem **kritiky** (porovnání s `DNA.md`) a **revize**, což vede k mnohem hlubšímu a bezpečnějšímu rozhodování.

* **`agents/` (Hybridní Agentní Model)**:
    * **Technologie:** `CrewAI` a `AutoGen`
    * **Funkce:** Systém bude využívat dva týmy agentů pro různé kognitivní funkce:
        * **Exekuční Tým (CrewAI):** Agenti jako `Planner`, `Engineer`, `Tester` budou fungovat v disciplinovaném, procesně orientovaném rámci `CrewAI` během fáze "Bdění" pro efektivní plnění úkolů.
        * **Kreativní Tým (AutoGen):** Agenti jako `Philosopher`, `Architect` budou fungovat ve flexibilním, konverzačním rámci `AutoGen` během fáze "Spánku" pro generování nových nápadů, sebereflexi a strategické plánování.

    * **LLM Integrace:**
        * Všichni agenti používají jednotný adapter `GeminiLLMAdapter` (viz `core/gemini_llm_adapter.py`), který zajišťuje robustní a snadno vyměnitelnou integraci s Google Gemini API.
        * Adapter je inicializován v `core/llm_config.py` dle konfigurace v `config.yaml` a předáván agentům jako `llm=llm`.
        * Přepnutí na jiného providera (např. OpenAI, LangChain) je možné úpravou konfigurace a jednoho řádku v `llm_config.py`.

        * **Quality Assurance Tým (Reviewer Agent):**
            * Pro zajištění kvality a udržitelnosti je zaveden `Reviewer Agent`.
            * **Funkce:** Tento agent automaticky kontroluje, zda jsou změny v kódu (`.py` soubory) doprovázeny odpovídajícími změnami v dokumentaci (`WORKLOG.md`). Působí jako automatizovaný recenzent, který vynucuje disciplínu v dokumentaci.


* **`/sandbox` (Izolované Prostředí)**:
    * **Funkce:** Bezpečný a izolovaný adresář, kde mohou agenti volně vytvářet, upravovat a spouštět soubory a kód, aniž by ovlivnili zbytek systému. Slouží jako testovací pole pro všechny tvůrčí úkoly.

* **`tools/` (Dílna pro Tvůrce)**:
    * **Technologie:** Vlastní implementace
    * **Funkce:** Bude obsahovat nové, klíčové nástroje pro agenty, jako `FileSystemTool` (pro práci se soubory v `/sandbox`) a `CodeExecutorTool` (pro spouštění a testování kódu).

* **`core/gemini_llm_adapter.py` (LLM Adapter):**
    * **Technologie:** `google-generativeai`
    * **Funkce:** Zajišťuje jednotné rozhraní pro všechny agenty a snadnou rozšiřitelnost na další LLM providery.

* **Testování a Spolehlivost (Robustní Testovací Prostředí)**:
    * **Technologie:** `pytest`, `monkeypatch`
    * **Funkce:** Systém je navržen pro maximální testovatelnost a spolehlivost.
        * **`SOPHIA_ENV`:** Proměnná prostředí, která přepíná mezi `production` a `test` režimem.
        * **`config_test.yaml`:** Oddělený konfigurační soubor, který se používá v `test` režimu. Umožňuje definovat specifické parametry pro testy (např. mockované LLM providery, jiné databázové spojení).
        * **`tests/conftest.py`:** Centrální bod pro řízení testů. Automaticky nastavuje `SOPHIA_ENV=test` a mockuje všechny externí služby (např. LLM volání) na úrovni `litellm.completion`, což zajišťuje, že testy jsou rychlé, izolované a nikdy neprovádějí reálné API volání.
