# Technický Plán Implementace: Replikace Agenta "Jules" v Projektu Sophia 2.0

**Verze:** 3.0
**Datum:** 2025-09-25
**Autor:** Jules (Nomad)

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

## 4. Správa Skriptů

Projekt musí obsahovat dva klíčové skripty pro správu prostředí.

-   **4.1 Vývojářský Setup Skript (`setup.sh` nebo `bootstrap.sh`):**
    -   **Účel:** Zajištění konzistentního a funkčního prostředí pro vývojáře (včetně AI agentů).
    -   **Funkce:**
        -   Ověření přítomnosti a verzí klíčových nástrojů (Python, uv, node).
        -   Vytvoření/aktivace virtuálního prostředí (`.venv`).
        -   Instalace závislostí z `requirements.in` pomocí `uv` (s fallbackem na `pip`).
        -   Spuštění ověřovacích testů pro potvrzení funkčnosti prostředí.
    -   **Udržba:** Tento skript musí být aktivně udržován a aktualizován s každou změnou v závislostech nebo konfiguraci prostředí.

-   **4.2 Uživatelský Instalační Skript (`install.sh`):**
    -   **Účel:** Poskytnout novým uživatelům co nejjednodušší a nejodolnější způsob, jak projekt nainstalovat a nakonfigurovat.
    -   **Funkce:**
        -   **Interaktivita:** Skript musí být plně interaktivní. Bude se uživatele ptát na klíčové informace.
        -   **Nastavení API Klíče:** Interaktivně si vyžádá `GOOGLE_API_KEY` a bezpečně ho uloží do `.env` souboru. Nesmí ho zobrazovat na terminálu.
        -   **Ověření API Klíče:** Po zadání klíče se pokusí provést jednoduché testovací volání na Gemini API, aby ověřil jeho platnost.
        -   **Uvítací Skript:** Po úspěšné instalaci a ověření klíče spustí pod-skript, který pomocí Gemini API vygeneruje personalizovanou uvítací zprávu pro uživatele.
        -   **Chybové Stavy:** Musí elegantně handleovat případy, kdy uživatel klíč nezadá nebo je klíč neplatný, a nabídnout mu jasné instrukce, co dál.

## 5. Provozní Režimy a Testování

-   **5.1 Detekce Provozních Režimů:**
    -   Při startu musí aplikace (v `main.py` nebo orchestrátoru) ověřit stav Gemini API a nastavit globální proměnnou nebo stavový příznak na jednu z následujících hodnot: `ONLINE`, `OFFLINE`, `API_ERROR`.
        -   `ONLINE`: API klíč je přítomen a testovací volání bylo úspěšné.
        -   `OFFLINE`: API klíč není v `.env` souboru nalezen.
        -   `API_ERROR`: API klíč je přítomen, ale komunikace selhává (např. chyba autentizace, sítě).
    -   Aplikace a její komponenty musí na tyto režimy adekvátně reagovat (např. v `OFFLINE` režimu neumožnit spuštění úkolů vyžadujících LLM).

-   **5.2 Návrh Testů Kompatibilních s Režimy:**
    -   **Povinnost:** Ke každé nové funkci nebo modulu musí být vytvořeny jednotkové testy.
    -   **Offline Kompatibilita:** Všechny testy, které interagují s externími službami (zejména Gemini API), musí být navrženy tak, aby fungovaly i v offline režimu.
    -   **Mockování:** Pro testování v `OFFLINE` a `API_ERROR` režimech bude využita technika "mockování" (např. pomocí `unittest.mock`), kde se skutečné volání API nahradí předpřipravenou, simulovanou odpovědí. To umožní testovat logiku aplikace bez závislosti na síti nebo platném API klíči.

---
## **Příloha A: Detailní Specifikace Komponent**

Tato příloha detailně popisuje klíčové interní mechanismy, které musí být implementovány pro věrnou replikaci.

### A.1 Architektura Systémového Promptu ("Meta Prompt")

Systémový prompt je základní "ústava" agenta. Není to jen statický text, ale dynamicky sestavovaný blok informací, který je předán LLM v každém cyklu. Jeho struktura musí být následující:

1.  **Sekce 1: Identita a Hlavní Direktiva (Statická část)**
    -   Definuje, kdo agent je ("Jsi Jules, AI softwarový inženýr..."), jeho cíl a hlavní, neměnná pravidla (vždy použij nástroj, postupuj krok za krokem).

2.  **Sekce 2: Popis Formátu Odpovědi (Statická část)**
    -   Explicitně definuje, že odpověď musí být POUZE volání nástroje uzavřené ve specifických značkách (`<TOOL_CODE_START>` a `<TOOL_CODE_END>`). Musí obsahovat příklady pro oba typy syntaxe (standardní a DSL).

3.  **Sekce 3: Popis Dostupných Nástrojů (Dynamická část)**
    -   Tato sekce bude dynamicky generována `ToolExecutor`em. Bude obsahovat seznam názvů všech dostupných nástrojů a jejich docstringy, aby LLM věděl, co může použít a jak.

4.  **Sekce 4: Paměťové Soubory (Dynamická část)**
    -   Obsah souborů `JULES.md` a `AGENTS.md`. To poskytuje LLM kontext o jeho dlouhodobé paměti, osobnosti a pravidlech projektu.

5.  **Sekce 5: Historie Aktuálního Úkolu (Dynamická část)**
    -   Kompletní historie dosavadních akcí a jejich výsledků v rámci aktuálního úkolu. To umožňuje LLM navázat na předchozí kroky.

6.  **Sekce 6: Finální Instrukce (Statická část)**
    -   Krátká, finální instrukce, která shrnuje úkol, např. "Analyzuj historii a navrhni další krok jako JEDNO volání nástroje."

### A.2 Komunikační Formáty Nástrojů

Agent musí podporovat dva odlišné formáty volání nástrojů. `ToolExecutor` musí být schopen oba formáty správně zparsovat a vykonat.

1.  **Standardní Syntaxe (Python-like)**
    -   **Popis:** Používá se pro jednoduché nástroje s jedním nebo více argumenty na jednom řádku. Formát je `název_nástroje(argument1, "argument2", ...)`
    -   **Příklad:** `read_file("src/main.py")`
    -   **Parsování:** Lze použít regulární výrazy pro extrakci názvu nástroje a řetězce s argumenty, který se následně rozdělí podle čárky.

2.  **Speciální Syntaxe (DSL - Domain Specific Language)**
    -   **Popis:** Používá se pro komplexní nástroje, kde argumenty (často víceřádkové) následují po názvu nástroje na nových řádcích.
    -   **Příklad:**
        ```
        create_file_with_block
        cesta/k/souboru.txt
        První řádek obsahu.
        Druhý řádek obsahu.
        ```
    -   **Parsování:** `ToolExecutor` musí nejprve zkontrolovat, zda volání odpovídá standardní syntaxi. Pokud ne, rozdělí celý blok kódu podle odřádkování. První řádek je název nástroje, zbytek jsou argumenty.

### A.3 Specifikace Klíčových Metod Orchestrátoru

-   **`_build_prompt()`:**
    -   Musí implementovat logiku popsanou v sekci A.1. Postupně spojí všech 6 sekcí do jednoho finálního textového řetězce, který bude odeslán do Gemini API.

-   **`_parse_tool_call()`:**
    -   Tato metoda musí nejprve z odpovědi LLM extrahovat obsah mezi značkami (`<TOOL_CODE_START>` a `<TOOL_CODE_END>`).
    -   Extrahovaný text je pak předán `ToolExecutoru`, který se postará o detailní parsování a vykonání. Orchestrátor tedy nemusí znát detaily syntaxe jednotlivých nástrojů.