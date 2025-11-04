# Roadmap 01: Implementace MVP - Rozšiřitelné Jádro

Tento dokument definuje přesný, krok-za-krokem postup pro implementaci Minimálního Životaschopného Produktu (MVP) Sophie. Cílem této roadmapy je vytvořit stabilní, testovatelné a rozšiřitelné Jádro a vybavit ho základními pluginy pro smysluplnou interakci.

Po dokončení této roadmapy bude Sophia schopna:
*   Být spravována stabilním, "zamčeným" Jádrem.
*   Automaticky načítat nové schopnosti (pluginy).
*   Komunikovat přes terminál a základní webové rozhraní.
*   Udržovat krátkodobou (session) a dlouhodobou (sémantickou) paměť.

---

### Krok 1: Vytvoření Skeletu Jádra a Kontraktu pro Pluginy

*   **Cíl:** Definovat neměnnou strukturu a rozhraní, na kterých bude stát celý systém.
*   **Klíčové Komponenty k Vytvoření:**
    *   `core/kernel.py`: Prázdná třída `Kernel`.
    *   `core/plugin_manager.py`: Prázdná třída `PluginManager`.
    *   `core/context.py`: Datová třída `SharedContext` s definovanými poli.
    *   `plugins/base_plugin.py`: Abstraktní třída `BasePlugin` definující kontrakt (jméno, typ, `setup`, `execute`).
*   **Ověřitelný Výsledek:** Adresářová struktura `core/` a `plugins/` existuje. Soubory obsahují kostry tříd a rozhraní. Kód není funkční, ale definuje architekturu.

### Krok 2: Implementace Dynamického `PluginManageru`

*   **Cíl:** Oživit `PluginManager` tak, aby dokázal automaticky najít, validovat a načíst pluginy.
*   **Klíčové Komponenty k Implementaci:**
    *   `core/plugin_manager.py`: Logika, která při startu proskenuje adresář `plugins/`, importuje moduly a registruje všechny třídy dědící z `BasePlugin`.
*   **Ověřitelný Výsledek:** `PluginManager` je testovatelný. Po vytvoření testovacího souboru `plugins/dummy_plugin.py` ho `PluginManager` dokáže najít a správně zaregistrovat.

### Krok 3: Implementace Jádra a Prvního "Interface" Pluginu (Terminál)

*   **Cíl:** Zprovoznit životní cyklus v Jádru a umožnit první, nejjednodušší formu interakce.
*   **Klíčové Komponenty k Implementaci:**
    *   `core/kernel.py`: Implementace `ConsciousnessLoop`, která řídí stavy a volá pluginy.
    *   `plugins/interface_terminal.py`: První skutečný plugin typu `INTERFACE`. Jeho metoda `execute` čeká na `input()` z terminálu a výsledek zapíše do `context.user_input`.
*   **Ověřitelný Výsledek:** Po spuštění `run.py` se Jádro nastartuje, načte terminálový plugin a čeká na vstup od uživatele. Po zadání textu se smyčka protočí a čeká znovu. Systém "žije".

### Krok 4: Přidání Myšlení a Krátkodobé Paměti

*   **Cíl:** Umožnit Sophii vést souvislý dialog a pamatovat si jej v rámci jednoho sezení.
*   **Klíčové Komponenty k Vytvoření:**
    *   `plugins/tool_llm.py`: Plugin typu `TOOL`, který vezme data z kontextu (`user_input`, `history`), zavolá externí LLM API a odpověď zapíše do kontextu.
    *   `plugins/memory_sqlite.py`: Plugin typu `MEMORY`. Na konci cyklu uloží aktuální interakci (vstup i odpověď) do SQLite databáze pod `session_id`. Při startu sezení načte relevantní historii.
*   **Ověřitelný Výsledek:** Plně funkční konverzační bot v terminálu, který udržuje kontext a ukládá historii konverzace do databáze.

### Krok 5: Důkaz Rozšiřitelnosti - Druhý "Interface" Plugin (Web UI)

*   **Cíl:** Dokázat sílu architektury přidáním nového rozhraní **bez jakékoliv změny v `core/`**.
*   **Klíčové Komponenty k Vytvoření:**
    *   `plugins/interface_webui.py`: Plugin typu `INTERFACE`, který při `setup` spustí na pozadí jednoduchý FastAPI server s WebSocketem pro real-time komunikaci.
*   **Ověřitelný Výsledek:** Sophia je dostupná a schopná vést dialog zároveň přes terminál i přes webové rozhraní. To potvrzuje, že Jádro je skutečně modulární.

### Krok 6: Přidání Dlouhodobé Paměti a Dokončení MVP

*   **Cíl:** Dát Sophii schopnost učit se z minulých konverzací a vytvářet si sémantickou bázi znalostí.
*   **Klíčové Komponenty k Vytvoření:**
    *   `plugins/memory_chroma.py`: Plugin typu `MEMORY`. Bude obsahovat logiku, která na konci sezení analyzuje konverzaci. Pokud identifikuje klíčový poznatek, vytvoří pro něj embedding a uloží ho do vektorové databáze ChromaDB.
*   **Ověřitelný Výsledek:** MVP je hotové. Sophia má stabilní jádro, více komunikačních kanálů a funkční krátkodobou i dlouhodobou paměť, čímž je připravena na další rozvoj a učení.