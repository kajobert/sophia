# Inspirace pro Roadmapu MVP

Tento dokument mapuje zjištění z archivní analýzy přímo na kroky uvedené v roadmapě `01_MVP_IMPLEMENTATION.md`. Slouží jako praktický průvodce, který poskytuje konkrétní inspiraci a znovupoužitelné vzory pro každou fázi vývoje.

---

### Krok 1: Vytvoření Kostry Jádra a Kontraktu pro Pluginy

*   **Poznatek z Archivu (`sophia-archived`):** Soubor `memory_systems.py` ukázal sílu čistého a jednoduchého API, které skrývá složitější backend.
*   **Inspirace:** Abstraktní třída `BasePlugin` je ideálním místem pro vynucení tohoto vzoru. Kontrakt by měl být co nejjednodušší (např. `setup`, `execute`), což umožní, aby vnitřní složitost každého pluginu zůstala plně zapouzdřená.

---

### Krok 2: Implementace Dynamického `PluginManageru`

*   **Poznatek z Archivu (`nomad-archived`):** `MCPClient` byl primitivní manažer pluginů, který spouštěl nástroje jako samostatné procesy. To zdůrazňuje potřebu centrální komponenty pro správu a volání schopností.
*   **Inspirace:** Ačkoli náš `PluginManager` bude načítat moduly přímo, role `MCPClient` jako jediného vstupního bodu pro provádění nástrojů je dobrým modelem. `PluginManager` by měl být *jedinou* komponentou, která ví, jak objevovat, validovat a spouštět pluginy. `Kernel` by měl být o těchto detailech zcela nevědomý a jednoduše požádat `PluginManager` o spuštění pluginu podle jména.

---

### Krok 3: Implementace Jádra a Prvního "Interface" Pluginu (Terminál)

*   **Poznatek z Archivu (`nomad-archived`):** Proaktivní stavový automat `NomadOrchestratorV2` (`THINKING` -> `EXECUTE`) je produkčně ověřený model pro hlavní smyčku agenta.
*   **Inspirace:** Měli bychom implementovat `ConsciousnessLoop` v `core/kernel.py` přesně podle tohoto vzoru. Je to jednoduchý, robustní a osvědčený design. Plugin `plugins/interface_terminal.py` bude zodpovědný za volání `input()` a `print()`, a bude předávat vstup uživatele do `SharedContext` pro zpracování smyčkou `Kernelu`.

---

### Krok 4: Přidání Myšlení a Krátkodobé Paměti

*   **Poznatek z Archivu (`nomad-archived`):** Metody `_build_prompt` a `_parse_llm_response` poskytují v praxi ověřený kód pro interakci s LLM.
*   **Inspirace pro `plugins/tool_llm.py`:** Tento plugin by měl být postaven na těchto konceptech. Bude číst cíl a historii z `SharedContext`, sestavovat strukturovaný prompt pomocí vzoru `build_system_prompt`, provádět volání a parsovat JSON odpověď pomocí regexového vzoru `parse_llm_json_response`.

*   **Poznatek z Archivu (`sophia-archived`):** Třída `ShortTermMemory` poskytuje čisté API pro klíč-hodnotové úložiště založené na session.
*   **Inspirace pro `plugins/memory_sqlite.py`:** Tento plugin by měl implementovat jednoduché API z třídy `ShortTermMemory` (`get`, `set`, `update`, `clear`), ale s backendem v SQLite namísto slovníku v paměti. `session_id` se bude mapovat přímo na název tabulky nebo na primární klíč v tabulce.

---

### Krok 5: Důkaz Rozšiřitelnosti - Druhý "Interface" Plugin (Web UI)

*   **Poznatek z Archivu (`nomad-archived`):** `README.md` pro tento projekt popisoval plnohodnotný FastAPI backend s WebSocket streamingem pro Textual TUI.
*   **Inspirace pro `plugins/interface_webui.py`:** Máme jasný precedent, že je to možné a efektivní. Tento plugin by měl zapouzdřit lehký FastAPI server. Metoda `setup` spustí server v pozadí a metoda `execute` bude zpracovávat předávání zpráv mezi WebSocketem a `SharedContext`. Existence tohoto v předchozí verzi nám dává vysokou důvěru v tento cíl rozšiřitelnosti.

---

### Krok 6: Přidání Dlouhodobé Paměti a Dokončení MVP

*   **Poznatek z Archivu (`sophia-old-archived`):** Nejranější prototyp používal `ChromaDB` pro dlouhodobou paměť a měl proces "snění" pro konsolidaci paměti.
*   **Inspirace pro `plugins/memory_chroma.py`:**
    *   API pluginu by mělo kopírovat jednoduché metody `add_record` a `search` z placeholder třídy `LongTermMemory`.
    *   Ačkoli plný proces "snění" je mimo rozsah MVP, měli bychom plugin navrhnout s touto budoucí schopností na paměti. To znamená, že funkce `add_record` by měla ukládat nejen text, ale i bohatá metadata (např. `session_id`, `timestamp`, `typ_paměti`), která by byla potřebná pro budoucí proces konsolidace.
