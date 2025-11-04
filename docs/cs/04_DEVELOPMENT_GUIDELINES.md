# Dokument 4: Vývojářské Směrnice

Tyto směrnice jsou povinné pro veškerý vývoj, aby byla zajištěna kvalita, konzistence a udržitelnost kódu.

## 1. Styl a Kvalita Kódu

*   **PEP 8:** Veškerý Python kód musí dodržovat styl popsaný v [PEP 8](https://www.python.org/dev/peps/pep-0008/).
*   **Formátování:** Používáme `black` pro automatické formátování kódu. Veškerý kód musí být před odevzdáním (commit) zformátován.
*   **Linting:** Používáme `ruff` k odhalení běžných chyb a stylistických problémů. Kód musí být bez chyb z linteru.

## 2. Typové Anotace

*   **100% Typově Anotováno:** Všechny funkce, metody a proměnné musí mít explicitní typové anotace v souladu s [PEP 484](https://www.python.org/dev/peps/pep-0484/).
*   **Statická Analýza:** Používáme `mypy` k vynucení typové správnosti. Váš kód musí projít kontrolou `mypy` bez chyb.

## 3. Docstringy a Komentáře

*   **Google Style Docstrings:** Všechny moduly, třídy, funkce a metody musí mít komplexní docstringy podle [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
*   **Jasnost před Vtipností:** Pište jasné a stručné komentáře tam, kde účel kódu není okamžitě zřejmý. Vyhněte se zbytečným nebo rušivým komentářům.

## 4. Jazyk a Lokalizace

*   **Pouze Angličtina:** Veškerý kód, včetně komentářů, docstringů, názvů proměnných a logovacích zpráv, **musí být psán v angličtině**.
*   **Důvod:** Jedná se o univerzální standard ve vývoji softwaru, který zajišťuje, že projekt je přístupný co nejširšímu publiku vývojářů a přispěvatelů.
*   **Dokumentace:** Uživatelská dokumentace může být dvojjazyčná a nachází se v adresářích `docs/en/` a `docs/cs/`.

## 5. Správa Konfigurace a Tajemství

Pro zajištění bezpečnosti, centralizace a snadné správy platí následující pravidlo:

**Pluginy nikdy nespravují vlastní konfiguraci ani nečtou konfigurační soubory či proměnné prostředí přímo.**

*   **Princip Vkládání Závislostí (Dependency Injection):**
    1.  Veškerá konfigurace (API klíče, cesty, přepínače) je definována **pouze** v centrálním konfiguračním souboru (např. `config/settings.yaml`).
    2.  **`PluginManager`** je jediná komponenta odpovědná za čtení této konfigurace.
    3.  Během inicializace pluginu (v rámci jeho metody `setup()`) mu `PluginManager` předá všechny potřebné konfigurační hodnoty, které daný plugin vyžaduje.
    4.  Plugin tedy dostane své "nastavení" zvenčí a nikdy se nestará o to, odkud pochází.

*   **Výhody:**
    *   **Bezpečnost:** API klíče a další citlivá data jsou centralizována, nikoli roztroušena po kódu pluginů.
    *   **Centralizace:** Když je třeba změnit parametr, děje se tak na jediném místě.
    *   **Testovatelnost:** Během testování můžeme snadno podstrčit falešnou (mock) konfiguraci do pluginu, aniž bychom museli manipulovat se soubory.

## 6. Údržba Dokumentace

**Pravidlo:** Kód není kompletní, dokud není aktualizována dokumentace.

*   **Povinné Aktualizace:** Každá změna kódu, která zavádí novou funkci, mění stávající chování nebo upravuje proces nastavení, **musí** být doprovázena odpovídající aktualizací dokumentace.
*   **Zodpovědnost:** Vývojář provádějící změnu kódu je zodpovědný za aktualizaci všech relevantních dokumentů.
*   **Dvojjazyčná Synchronizace:** Veškerá dokumentace musí být udržována v souladu mezi anglickou (`docs/en/`) a českou (`docs/cs/`) verzí. Anglická verze je považována za zdroj pravdy.

## 7. Provádění vícekrokových plánů

Kernel je schopen provádět komplexní, vícekrokové plány generované `CognitivePlanner`. Tato funkcionalita se opírá o dva klíčové architektonické vzory:

### 7.1. Řetězení výsledků (Result Chaining)

Krok v plánu může použít výstup předchozího kroku jako jeden ze svých argumentů. Toho je dosaženo pomocí specifické syntaxe zástupných symbolů.

*   **Syntaxe:** `"$result.step_N"`
*   **Příklad:** Pokud je Krok 1 `list_plugins()` a Krok 2 je `write_file()`, plán může systému nařídit, aby zapsal výstup prvního kroku do souboru takto:
    ```json
    "arguments": {
        "path": "output.txt",
        "content": "$result.step_1"
    }
    ```
*   Kernel je zodpovědný za parsování této syntaxe, načtení uloženého výstupu z určeného kroku a jeho dosazení do argumentů před spuštěním nástroje.

### 7.2. Propagace kontextu s historií (History-Aware Context Propagation)

Aby byl vícekrokový plán úspěšný, musí mít pozdější kroky (zejména ty, které zahrnují LLM) přístup k výsledkům a akcím dřívějších kroků. Kernel to zajišťuje prostřednictvím **propagace kontextu s historií**.

*   **Mechanismus:** Před spuštěním *každého* kroku v plánu vytvoří Kernel nový, dočasný objekt `SharedContext` pro tento konkrétní krok.
*   **Obohacená historie:** Atribut `history` tohoto nového kontextu je kompletním záznamem sezení až do tohoto bodu. Obsahuje:
    1.  Původní požadavek uživatele.
    2.  Zprávy od "asistenta", které explicitně uvádějí výstup *všech předchozích provedených kroků* v aktuálním plánu.
*   **Vkládání kontextu:** Tento obohacený kontext s historií je poté vložen do volání nástroje pro aktuální krok (pokud signatura metody nástroje vyžaduje argument `context`).
*   **Důležitost:** Tím je zajištěno, že každý nástroj v řetězci má plný kontext nezbytný k provedení své funkce, což umožňuje agentovi uvažovat o a provádět komplexní, sekvenční úkoly.

## 8. Osvědčené postupy pro vývoj pluginů

Aby bylo zajištěno, že pluginy jsou robustní, udržovatelné a bezproblémově se integrují s Kernelem, jsou následující osvědčené postupy povinné.

### 8.1. Logování s ohledem na kontext

**Pravidlo:** Všechny logovací operace v rámci metod pluginu **musí** používat logger poskytovaný v objektu `SharedContext`. Nepoužívejte logger na úrovni modulu (`logging.getLogger(__name__)`).

*   **Mechanismus:** Kernel vkládá do `SharedContext` pro každou operaci logger specifický pro danou relaci. Použití `context.logger` zajišťuje, že všechny logovací zprávy jsou automaticky označeny správným `session_id`, což je klíčové pro ladění a sledování vícekrokových úkolů.

*   **Správný příklad:**
    ```python
    def my_tool_method(self, context: SharedContext, ...):
        context.logger.info("Provádím svou metodu.")
    ```

*   **Nesprávný příklad:**
    ```python
    import logging
    logger = logging.getLogger(__name__)

    def my_tool_method(self, ...):
        # Tomuto logu bude chybět session_id!
        logger.info("Provádím svou metodu.")
    ```

### 8.2. Explicitní návrh nástrojů pro AI

**Princip:** Při navrhování nástrojů pro AI vždy upřednostňujte maximální explicitnost. AI je jen tak dobrá, jaké informace dostane.

*   **Jasné pojmenování:** Názvy metod by měly být popisné a jednoznačné (např. `execute_command` je lepší než `run`).
*   **Detailní popisy:** Pole `description` pro funkci nástroje v `get_tool_definitions` by mělo jasně a stručně vysvětlovat, co nástroj dělá, k čemu slouží jeho parametry a co vrací.
*   **Nic nepředpokládejte:** Nepředpokládejte, že LLM "ví", co funkce dělá, jen na základě jejího názvu. Popis je jeho primárním zdrojem informací. Dobře navržený nástroj vyžaduje od LLM minimální "hádání", což vede ke spolehlivějším a předvídatelnějším plánům.
