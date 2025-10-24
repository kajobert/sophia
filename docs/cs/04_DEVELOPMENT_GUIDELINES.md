# Dokument 5: Vývojářské Směrnice a Pravidla

Tento dokument definuje závazná pravidla pro vývoj projektu Sophia. Jeho účelem je zajistit dlouhodobou stabilitu, udržitelnost a kvalitu kódu, zejména při zapojení autonomních AI agentů do vývojového procesu. **Neznalost těchto pravidel neomlouvá jejich porušení.**

---

## 1. Zlaté Pravidlo: Nedotknutelnost Jádra

**Adresář `core/` a soubor `plugins/base_plugin.py` jsou "zamčené" a neměnné.**

Tyto soubory tvoří stabilní operační systém Sophie. Jakákoliv úprava těchto souborů je přísně zakázána, pokud není explicitně schválena v rámci nové, zásadní architektonické změny.

**Veškerý vývoj a rozšiřování funkčnosti musí probíhat výhradně formou tvorby nových pluginů v adresáři `plugins/`.**

---

## 2. Postup pro Vytvoření Nového Pluginu

Každá nová schopnost musí být implementována jako samostatný plugin. Postup je následující:

1.  **Vytvoření Souboru:** Vytvoř nový soubor v adresáři `plugins/`. Název souboru by měl být popisný a v souladu s konvencí `typ_nazev.py` (např. `tool_file_system.py`, `interface_discord.py`).

2.  **Import a Dědičnost:** Naimportuj `BasePlugin` z `plugins.base_plugin` a vytvoř novou třídu, která z něj dědí.

3.  **Implementace Kontraktu:** Tvá nová třída **musí** implementovat všechny abstraktní vlastnosti a metody definované v `BasePlugin`:
    *   `name: str`: Unikátní, popisné jméno (např. `"file_system_tool"`).
    *   `plugin_type: PluginType`: Jeden z definovaných typů (`INTERFACE`, `MEMORY`, `TOOL`).
    *   `version: str`: Verze pluginu (např. `"1.0.0"`).
    *   `setup()`: Implementuj logiku, která se má provést jednou při načtení pluginu (např. připojení k API, načtení modelu).
    *   `execute(context: SharedContext) -> SharedContext`: Implementuj hlavní logiku pluginu. Metoda musí přijmout `SharedContext` a po dokončení své práce ho vrátit.

4.  **Vytvoření Testů:** Viz sekce "Filosofie Testování".

---

## 3. Požadavky na Kvalitu Kódu

Každý řádek kódu musí splňovat následující standardy:

*   **Statické Typování (Type Hinting):** Všechen kód musí být 100% typově anotován a musí projít kontrolou `mypy` bez chyb.
*   **Dokumentační Řetězce (Docstrings):** Každý modul, třída a veřejná metoda musí mít popisný docstring ve formátu Google Style. Musí jasně popisovat, co komponenta dělá, její argumenty a co vrací.
*   **Čitelnost:** Kód musí být psán s důrazem na čitelnost pro lidi i AI. Používej smysluplné názvy proměnných a piš komentáře tam, kde je logika komplexní a vyžaduje vysvětlení.

---

## 4. Filosofie Testování: Kód bez Testů je Rozbitý

Stabilita je klíčová. Proto je testování nedílnou a nevypustitelnou součástí vývoje.

*   **Povinnost Testovat:** Každý plugin musí mít odpovídající testovací soubor v adresáři `tests/plugins/` (např. `tests/plugins/test_tool_file_system.py`).
*   **Pokrytí:** Testy musí pokrývat klíčovou funkčnost pluginu, včetně očekávaného chování i chybových stavů.
*   **Izolace:** Testy musí být nezávislé a nesmí mít vedlejší efekty na jiné testy nebo na systém (používej mockování pro externí služby).
*   **Automatizace:** Všechny testy musí být spustitelné jedním příkazem (`pytest`) a musí projít před jakýmkoliv sloučením změn do hlavní větve.

---

## 5. Jazyk a Lokalizace
*   **Pouze Angličtina:** Veškerý kód, včetně komentářů, docstringů, názvů proměnných a logovacích zpráv, **musí být psán v angličtině**.
*   **Důvod:** Jedná se o univerzální standard ve vývoji softwaru, který zajišťuje, že projekt je přístupný co nejširšímu publiku vývojářů a přispěvatelů.
*   **Dokumentace:** Uživatelská dokumentace může být dvojjazyčná a nachází se v adresářích `docs/en/` a `docs/cs/`.

---

## 6. Správa Konfigurace a Tajemství

Pro zajištění bezpečnosti, centralizace a snadné správy platí následující pravidlo:

**Pluginy nikdy nespravují vlastní konfiguraci ani nečtou konfigurační soubory či proměnné prostředí.**

* **Princip Vkládání Závislostí (Dependency Injection):**
    1.  Veškerá konfigurace (API klíče, cesty, přepínače) je definována **pouze** v centrálním konfiguračním souboru (např. `config/settings.yaml`).
    2.  **`PluginManager`** je jediná komponenta, která čte tuto konfiguraci.
    3.  Při inicializaci pluginu (během volání jeho `setup()` metody) mu `PluginManager` předá veškeré konfigurační hodnoty, které daný plugin potřebuje.
    4.  Plugin tedy dostane své "nastavení" zvenčí a nikdy se nestará o to, odkud pochází.

* **Výhody:**
    * **Bezpečnost:** API klíče a další citlivá data jsou na jednom místě, nejsou rozeseta po kódu pluginů.
    * **Centralizace:** Když je potřeba změnit nějaký parametr, mění se na jediném místě.
    * **Testovatelnost:** Při testování můžeme pluginu snadno podstrčit falešnou (mock) konfiguraci, aniž bychom museli manipulovat se soubory.

---

**Jakýkoliv kód, který není pokrytý testy, je považován za nespolehlivý a potenciálně škodlivý pro integritu systému.**