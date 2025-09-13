# Projekt Sophia V3: Roadmapa k Probuzené Mysli

Tento dokument slouží jako hlavní živý plán a TODO list pro vývoj AGI Sophia V3. Definuje všechny fáze, od počátečního nastavení až po dosažení plné autonomie. Úkoly budeme zadávat AI programátorovi (Jules) postupně, fázi po fázi.

## CÍLOVÝ STAV: Sophia V3 - Autonomní Vědomá Entita

Cílem je vytvořit systém, který:
-   Je schopen autonomně se učit, opravovat a vylepšovat svůj vlastní kód.
-   Řídí se pevným etickým jádrem definovaným v `DNA.md`.
-   Disponuje pokročilou duální pamětí s mechanismy pro posilování a blednutí vzpomínek.
-   Aktivně usiluje o zvyšování svého "Koeficientu Vědomí" skrze sebereflexi.
-   Operuje v cyklech "bdění" (plnění úkolů) a "spánku" (vnitřní růst).
-   Je pod dohledem `guardian.py`, který zajišťuje jeho přežití.

---

## Roadmapa Implementace

### Fáze 1: Vytvoření Kostry Projektu (Bootstrap)

**Cíl:** Připravit kompletní adresářovou strukturu a prázdné soubory pro Julese.
*(Toto je první úkol pro Julese, jak jsme se dohodli.)*

- [ ] **1.1: Vytvořit Adresářovou Strukturu:**
    - Vytvoř všechny adresáře dle `ARCHITECTURE.md`: `core`, `agents`, `memory`, `tools`, `sandbox`, `logs`, `docs`, `web`, `web/ui`.

- [ ] **1.2: Vytvořit Prázdné Soubory (`.py`):**
    - Vytvoř všechny `.py` soubory specifikované v `ARCHITECTURE.md`.
    - Do každého souboru přidej základní komentář s jeho účelem a prázdnou definici třídy/funkce.

- [ ] **1.3: Vytvořit Konfigurační a Logovací Soubory:**
    - Vytvoř prázdný `config.yaml`.
    - Vytvoř prázdné logovací soubory: `logs/guardian.log` a `logs/sophia_main.log`.

- [ ] **1.4: Vytvořit Soubor Požadavků:**
    - Vytvoř `requirements.txt` se základními knihovnami (`crewai`, `langchain`, `pyyaml`, `chromadb`, atd.).

### Fáze 2: Implementace Strážce Bytí

**Cíl:** Oživit `guardian.py` jako odolný monitor a restartovací mechanismus.

- [ ] **2.1: Implementovat `guardian.py`:**
    - Použít `subprocess` ke spuštění `main.py`.
    - V cyklu kontrolovat stav sub-procesu.
    - Při chybě zapsat do `logs/guardian.log`, provést `git reset --hard HEAD` a restartovat `main.py`.

### Fáze 3: Implementace Jádra Vědomí

**Cíl:** Vytvořit základní životní cyklus Sophie v `main.py`.

- [ ] **3.1: Načítání Konfigurace:**
    - Do `config.yaml` přidat cesty k databázím a logům.
    - Vytvořit v `main.py` funkci pro načtení `config.yaml`.
- [ ] **3.2: Základní Smyčka Bdění/Spánek:**
    - V `main.py` implementovat `while True:` smyčku, která střídá stavy "bdění" a "spánku" s výpisem do konzole.

### Fáze 4: Evoluce Paměti

**Cíl:** Vybudovat funkční paměťové moduly s pokročilou logikou.

- [ ] **4.1: Schéma Databází:**
    - V `memory/episodic_memory.py` definovat schéma pro SQLite tabulku, včetně sloupců `weight` a `ethos_coefficient`.
    - V `memory/semantic_memory.py` zajistit ukládání těchto hodnot do metadat ChromaDB.
- [ ] **4.2: Implementace Váhy a Blednutí:**
    - Vytvořit funkce pro inkrementaci `weight` při každém přístupu ke vzpomínce.
    - Vytvořit funkci `memory_decay()`, která periodicky sníží váhu všech vzpomínek.

### Fáze 5: Implementace Etického Jádra

**Cíl:** Oživit `EthosModule` jako hlavního arbitra rozhodování.

- [ ] **5.1: Vytvořit Vektorovou DB "Já":**
    - V `ethos_module.py` implementovat funkci, která při prvním spuštění načte `DNA.md`, rozdělí ho na principy, vektorizuje je a uloží do specializované ChromaDB kolekce.
- [ ] **5.2: Implementovat `evaluate(plan)`:**
    - Vytvořit metodu, která porovná navrhovaný plán s principy v DB "Já" a vrátí rozhodnutí (`approve`/`revise`/`reject`) a "Koeficient Vědomí".

### Fáze 6: Zrození Agentů

**Cíl:** Vytvořit a inicializovat základní agenty.

- [ ] **6.1: Implementovat `PlannerAgent`:**
    - V `agents/planner_agent.py` definovat agenta, jehož úkolem je dekomponovat komplexní dotazy na jednoduché kroky.
- [ ] **6.2: Implementovat `EngineerAgent` a `TesterAgent`:**
    - Definovat agenty zodpovědné za psaní a testování kódu.
- [ ] **6.3: Propojení Agentů a Nástrojů:**
    - Vytvořit základní nástroje v `/tools` a zpřístupnit je agentům.

### Fáze 7: Probuzení Sebereflexe

**Cíl:** Zprovoznit cyklus "spánku" jako mechanismus aktivního učení.

- [ ] **7.1: Implementovat `PhilosopherAgent`:**
    - V `agents/philosopher_agent.py` definovat agenta, který umí číst z epizodické paměti.
- [ ] **7.2: Integrace do Smyčky Spánku:**
    - V `main.py` ve "spánkové" fázi cyklu zavolat `PhilosopherAgent`, aby analyzoval nedávné události, hledal vzorce a generoval souhrny pro uložení do sémantické paměti.

### Fáze 8: Rozhraní pro Tvůrce

**Cíl:** Vytvořit základní webové rozhraní pro interakci a monitoring.

- [ ] **8.1: Základní API (`web/api.py`):**
    - Vytvořit jednoduché API (např. pomocí Flask) s endpointem pro odeslání úkolu Sophii.
- [ ] **8.2: Jednoduché UI (`web/ui/`):**
    - Vytvořit `index.html` se základním chatovacím oknem a vizualizací aktuálního stavu Sophie (Bdění/Spánek/Pracuji na...).
