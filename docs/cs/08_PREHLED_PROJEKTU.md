# Sophia V2 - Přehled projektu

Tento dokument poskytuje celkový přehled projektu Sophia V2, jeho architektury a dlouhodobých cílů. Je zamýšlen jako rychlá reference pro vlastníka projektu.

## 1. Rychlý přehled příkazů

Zde je "tahák" nejběžnějších příkazů pro správu projektu:

-   **Nastavení pro uživatele (první spuštění):**
    ```bash
    uv venv && source .venv/bin/activate && uv pip sync requirements.in
    ```

-   **Nastavení pro vývojáře (první spuštění):**
    ```bash
    uv venv && source .venv/bin/activate && uv pip install -r requirements.in -r requirements-dev.in
    ```

-   **Aktivace virtuálního prostředí:**
    ```bash
    source .venv/bin/activate
    ```

-   **Instalace/aktualizace závislostí (Uživatel):**
    ```bash
    uv pip sync requirements.in
    ```

-   **Instalace/aktualizace závislostí (Vývojář):**
    ```bash
    uv pip install -r requirements.in -r requirements-dev.in
    ```

-   **Spuštění aplikace (terminál a webové rozhraní):**
    ```bash
    python run.py
    ```

-   **Spuštění testů:**
    ```bash
    PYTHONPATH=. .venv/bin/python -m pytest
    ```

-   **Spuštění kontrol kvality kódu a formátování:**
    ```bash
    pre-commit run --all-files
    ```

## 2. Architektura a tok dat

Sophia V2 je postavena na modulární, asynchronní architektuře typu jádro-plugin, navržené pro snadnou rozšiřitelnost.

### 2.1. Klíčové komponenty

-   **`run.py`:** Hlavní vstupní bod aplikace. Inicializuje a spouští jádro (Kernel).
-   **`core/kernel.py`:** Srdce aplikace. Obsahuje `consciousness_loop` (smyčku vědomí), která řídí jednotlivé fáze operací (Naslouchání, Myšlení, Reagování, Ukládání do paměti). Je zodpovědný za načítání, konfiguraci a spouštění pluginů.
-   **`core/plugin_manager.py`:** Objevuje a načítá všechny platné pluginy z adresáře `plugins/`. Kategorizuje je podle typu (`INTERFACE`, `TOOL`, `MEMORY`), aby je jádro mohlo používat.
-   **`core/context.py`:** Definuje datový objekt `SharedContext`. Tento objekt je životní krví aplikace, předává se mezi jádrem a pluginy v každém cyklu `consciousness_loop`. Nese uživatelský vstup, historii konverzace a slovník `payload` pro mezipluginovou komunikaci.
-   **`plugins/base_plugin.py`:** Definuje abstraktní třídu `BasePlugin`, která slouží jako kontrakt pro všechny pluginy.

### 2.2. Tok dat v jednom cyklu

1.  **FÁZE NASLOUCHÁNÍ (LISTENING):**
    -   Spustí se `consciousness_loop` jádra.
    -   Zavolá metodu `execute` na všech `INTERFACE` pluginech (např. `TerminalInterface`, `WebUIInterface`).
    -   Tyto pluginy čekají na vstup od uživatele (např. z příkazové řádky nebo WebSocketu).
    -   Po obdržení vstupu jej plugin vloží do `context.user_input` a v případě webového rozhraní přidá funkci `_response_callback` do `context.payload`.
    -   První rozhraní, které obdrží vstup, dokončí svůj úkol a smyčka přejde do další fáze.

2.  **FÁZE MYŠLENÍ (THINKING):**
    -   Jádro iteruje přes všechny `TOOL` pluginy (např. `LLMTool`).
    -   `LLMTool` vezme `context.history` (která nyní obsahuje nový vstup uživatele), odešle ji do nakonfigurovaného LLM a výsledek uloží do `context.payload["llm_response"]`.

3.  **FÁZE REAGOVÁNÍ (RESPONDING):**
    -   Jádro vytiskne `llm_response` do konzole pro terminálové rozhraní.
    -   Poté zkontroluje, zda v `context.payload` existuje `_response_callback`. Pokud ano (tj. vstup přišel z webového rozhraní), zavolá tuto funkci, která odešle odpověď zpět přes příslušné WebSocket spojení.

4.  **FÁZE UKLÁDÁNÍ DO PAMĚTI (MEMORIZING):**
    -   Jádro iteruje přes všechny `MEMORY` pluginy (např. `SQLiteMemory`).
    -   Plugin `SQLiteMemory` vezme poslední zprávu od uživatele a odpověď AI z `context.history` a uloží je do databáze.

5.  **Čištění:**
    -   `context` je resetován pro další cyklus a smyčka se opakuje.

## 3. Dlouhodobá vize a roadmapa

Cílem tohoto projektu je vyvinout sofistikovanou, rozšiřitelnou umělou obecnou inteligenci (AGI) jménem Sophia V2. Architektura je navržena tak, aby se vyvíjela v jednotlivých fázích.

### Fáze 1: Implementace MVP (aktuální)
-   **Cíl:** Vytvořit stabilní jádro architektury a základní sadu funkčních pluginů.
-   **Kroky:**
    1.  Základní kostra a kontrakt pluginu **(Hotovo)**
    2.  Dynamický Plugin Manager **(Hotovo)**
    3.  Jádro a terminálové rozhraní **(Hotovo)**
    4.  Myšlení a krátkodobá paměť **(Hotovo)**
    5.  Webové UI rozhraní **(Hotovo)**
    6.  **[Další]** Základní nástroj pro práci se souborovým systémem

### Fáze 2: Integrace a rozšíření nástrojů
-   **Cíl:** Rozšířit schopnosti Sophie přidáním dalších nástrojů a zlepšením jejich používání.
-   **Klíčové oblasti:**
    -   Schopnost vyhledávání na internetu.
    -   Spouštění kódu a interakce se souborovým systémem.
    -   Dlouhodobá paměť a získávání znalostí (např. pomocí vektorových databází).
    -   Sofistikovanější plánování a rozklad úkolů.

### Fáze 3: Sebeanalýza a zlepšování
-   **Cíl:** Umožnit Sophii analyzovat svůj vlastní výkon a navrhovat vylepšení.
-   **Klíčové oblasti:**
    -   Logování a metrika pro všechny akce.
    -   "Meta-plugin", který dokáže revidovat logy a data o výkonu.
    -   Schopnost navrhovat nebo dokonce psát úpravy kódu pro sebe sama.

### Fáze 4: Autonomní operace
-   **Cíl:** Dosáhnout vyššího stupně autonomie, což Sophii umožní fungovat s menším přímým lidským dohledem.
-   **Klíčové oblasti:**
    -   Proaktivní dosahování cílů.
    -   Běh jako nepřetržitá, dlouhodobá služba.
    -   Složitější provádění vícekrokových úkolů.
