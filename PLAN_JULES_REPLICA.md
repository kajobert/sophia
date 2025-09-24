# Technický Plán Implementace: Replikace Agenta "Jules" v Projektu Sophia 2.0

**Verze:** 1.0
**Datum:** 2025-09-24
**Autor:** Jules (AI Agent)

## 1. Cíl a Strategie

Cílem je vytvořit plně funkčního AI agenta, který replikuje chování, architekturu a pracovní postupy agenta "Jules". Implementace bude provedena v Pythonu s využitím Google Gemini API (model `gemini-1.5-flash-latest`).

Strategie spočívá ve vytvoření modulárního systému, který striktně odděluje:
1.  **Řídící logiku** (Orchestrátor).
2.  **Definici a vykonávání nástrojů** (Tool Executor).
3.  **Základní "osobnost" a pravidla** (Systémový Prompt).
4.  **Konfiguraci a paměť** (YAML a .md soubory).

## 2. Požadované Technologie a Závislosti

-   **Jazyk:** Python 3.11+
-   **API:** `google-generativeai`
-   **Konfigurace:** `PyYAML`
-   **Správa klíčů:** `python-dotenv`
-   **Správce závislostí:** `uv` nebo `pip`

## 3. Fáze Implementace

### Fáze 1: Základy Projektu a Konfigurace (Scaffolding)

**Cíl:** Připravit čistou a škálovatelnou adresářovou strukturu a konfiguraci.

-   **Akce 1.1: Vytvořit Adresářovou Strukturu:**
    -   `sophia_jules_replica/` (hlavní adresář)
    -   `├── core/` (pro hlavní logiku: orchestrátor, executor)
    -   `├── tools/` (pro jednotlivé moduly s nástroji)
    -   `├── memory/` (pro `JULES.md` a `AGENTS.md`)
    -   `├── config/` (pro konfigurační soubory)
    -   `└── main.py` (vstupní bod aplikace)

-   **Akce 1.2: Definovat Závislosti:**
    -   Vytvořit `requirements.in` se závislostmi: `google-generativeai`, `python-dotenv`, `PyYAML`.

-   **Akce 1.3: Nastavit Konfiguraci:**
    -   Vytvořit `config/config.yaml` pro parametry modelu (`model_name`, `temperature`) a cesty k paměťovým souborům.
    -   Vytvořit `.env.example` a `.gitignore` pro správu `GOOGLE_API_KEY` a ignorování nepotřebných souborů.

-   **Akce 1.4: Naplnit Paměť:**
    -   Zkopírovat existující, finální verze souborů `JULES.md` a `AGENTS.md` do adresáře `memory/`.

### Fáze 2: Implementace Jádra Orchestrátoru

**Cíl:** Vytvořit centrální mozek agenta – třídu, která řídí jeho životní cyklus.

-   **Akce 2.1: Vytvořit Třídu `JulesOrchestrator` v `core/orchestrator.py`:**
    -   **`__init__`:** Načte konfiguraci, API klíč, paměťové soubory a inicializuje klienta Gemini. Bude udržovat interní seznam `history` pro ukládání všech akcí a jejich výsledků.
    -   **Metoda `_build_prompt()`:** Bude dynamicky sestavovat kompletní prompt pro LLM z historie, systémového promptu a obsahu paměťových souborů.
    -   **Metoda `_parse_tool_call()`:** Bude zodpovědná za spolehlivé parsování textové odpovědi z LLM a extrakci bloku s kódem pro volání nástroje.
    -   **Metoda `run()`:** Bude obsahovat hlavní `while` smyčku agenta. V každé iteraci zavolá `_build_prompt()`, odešle dotaz na Gemini API, zparsuje odpověď a předá volání nástroje `ToolExecutoru`.

### Fáze 3: Abstrakce a Implementace Nástrojů

**Cíl:** Vytvořit flexibilní a rozšiřitelný systém pro definování a vykonávání nástrojů.

-   **Akce 3.1: Vytvořit Třídu `ToolExecutor` v `core/tool_executor.py`:**
    -   **`__init__`:** Bude dynamicky skenovat adresář `tools/`, importovat všechny nalezené moduly a registrovat všechny funkce (nástroje) do interního slovníku.
    -   **Metoda `execute_tool()`:** Přijme zparsovaný řetězec s voláním nástroje, najde odpovídající funkci ve svém registru a bezpečně ji vykoná s danými argumenty. Bude vracet výstup nástroje jako text.

-   **Akce 3.2: Implementovat Moduly s Nástroji v `tools/`:**
    -   Vytvořit samostatné soubory pro logicky související nástroje (např. `tools/file_system.py`, `tools/shell.py`).
    -   Každý nástroj bude implementován jako samostatná funkce, která přijímá argumenty a vrací textový výstup (včetně případných chyb).

### Fáze 4: Definice Systémového Promptu ("Osobnosti")

**Cíl:** Vytvořit sadu základních instrukcí, která definuje chování a osobnost agenta.

-   **Akce 4.1: Vytvořit `core/system_prompt.py`:**
    -   Tento soubor bude obsahovat jednu konstantu `SYSTEM_PROMPT` (víceřádkový f-string).
    -   Prompt bude obsahovat klíčové direktivy z `JULES.md` (sekce Pravidla a Zákony, Architektura), popis formátu výstupu (striktně jen volání nástroje) a instrukce k uvažování krok za krokem.

### Fáze 5: Spojení a Spuštění

**Cíl:** Vytvořit hlavní vstupní bod pro spuštění agenta s konkrétním úkolem.

-   **Akce 5.1: Implementovat `main.py`:**
    -   Skript bude používat `argparse` pro přijetí počátečního úkolu od uživatele z příkazové řádky.
    -   Načte `.env` soubor.
    -   Vytvoří instance `ToolExecutor` a `JulesOrchestrator`.
    -   Zavolá metodu `orchestrator.run()` a tím spustí hlavní smyčku agenta.

## 4. Ověření a Testování

-   Po dokončení každé fáze je doporučeno provést jednotkové testy pro ověření funkčnosti (např. testy pro `ToolExecutor`, parsování odpovědi).
-   Po dokončení implementace bude proveden end-to-end test s jednoduchým úkolem (např. "Vytvoř soubor `test.txt` s obsahem 'ahoj' a následně ho přečti.") pro ověření celého řetězce.