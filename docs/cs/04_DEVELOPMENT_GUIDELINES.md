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
