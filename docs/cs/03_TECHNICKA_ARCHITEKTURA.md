# Dokument 3: Technická architektura

Tento dokument popisuje technický návrh systému AGI Sophia se zaměřením na model Core-Plugin.

## 1. Základní filozofie: Stabilita a rozšiřitelnost

*   **Jádro je posvátné:** Jádro (`core`) aplikace je minimální, stabilní a chráněné. Poskytuje základní strukturu a orchestraci, ale neobsahuje žádnou doménově specifickou logiku.
*   **Vše je plugin:** Veškerá funkčnost, od kognitivních procesů po integraci nástrojů, je implementována jako samostatný plugin. Díky tomu je systém modulární, snadno testovatelný a bezpečně rozšiřitelný.

## 2. Hlavní komponenty

### 2.1. Jádro (`core/`)

*   **Odpovědnost:** Orchestruje hlavní smyčku aplikace, spravuje pluginy a řídí tok dat.
*   **Klíčové moduly:**
    *   `run.py`: Vstupní bod aplikace.
    *   `kernel.py`: Orchestruje hlavní smyčku aplikace (`Smyčka vědomí`), spravuje stav a řídí tok dat.
    *   `plugin_manager.py`: Objevuje, načítá a ověřuje pluginy.
    *   `context.py`: Definuje datovou strukturu `SharedContext`.
    *   `logging.py`: Konfiguruje centrální systém protokolování.

#### 2.1.1. Pokročilé funkce jádra

Jádro obsahuje několik pokročilých funkcí, které umožňují komplexní, více-krokové operace:

*   **Validační a opravná smyčka:** Před spuštěním nástroje jádro ověří argumenty poskytnuté AI proti schématu Pydantic. Pokud ověření selže, automaticky spustí "opravnou smyčku", která použije specializovaný LLM prompt k opravě chybných argumentů.
*   **Vkládání kontextu:** Jádro inteligentně prozkoumá signaturu metody nástroje. Pokud detekuje parametr `context`, automaticky vloží aktuální objekt `SharedContext`, čímž nástroji poskytne přístup k loggeru, ID sezení a historii konverzace.
*   **Propagace historie:** Pro každý krok ve více-krokovém plánu jádro vytvoří nový `SharedContext` s vědomím historie. Tento kontext zahrnuje původní požadavek uživatele plus výsledky všech předchozích kroků, což zajišťuje, že AI má úplné porozumění postupu úkolu.
*   **Strategický orchestrátor modelů:** Pro optimalizaci nákladů a výkonu používá jádro dvoufázový kognitivní proces. Před zavoláním hlavního `CognitivePlanner` analyzuje lehký `CognitiveTaskRouter` plugin požadavek uživatele. Používá rychlý a levný model k klasifikaci úkolu do předdefinované kategorie (např. `simple_query`, `plan_generation`). Na základě této klasifikace vybere nejvhodnější (např. nejlevnější nebo nejvýkonnější) model pro daný úkol ze strategie definované v `config/model_strategy.yaml`. Tím je zajištěno, že drahé, vysoce výkonné modely jsou použity pouze v případě nutnosti.

### 2.2. Pluginy (`plugins/`)

*   **Odpovědnost:** Zapouzdřuje specifickou část funkčnosti.
*   **Struktura:**
    *   Každý plugin je jeden soubor v Pythonu (např. `plugins/tool_file_system.py`).
    *   Každý plugin **musí** dědit z třídy `BasePlugin` definované v `plugins/base_plugin.py`.
    *   Pluginy jsou objevovány a načítány za běhu `PluginManagerem`.

#### 2.2.1. Dostupné nástrojové pluginy

*   **`FileSystemTool`:** Poskytuje bezpečné, izolované prostředí pro agenta ke čtení, zápisu a výpisu souborů. Všechny operace se soubory jsou omezeny na určený adresář `sandbox/`, aby se zabránilo neúmyslnému přístupu k systému.
*   **`BashTool`:** Umožňuje agentovi spouštět příkazy shellu v bezpečném, izolovaném prostředí. To je užitečné pro spouštění skriptů, správu procesů nebo interakci s operačním systémem kontrolovaným způsobem.
*   **`GitTool`:** Umožňuje agentovi interagovat s vlastním repozitářem zdrojového kódu. Může kontrolovat stav, zobrazovat rozdíly změn a získat název aktuální větve, což poskytuje základní úroveň sebeuvědomění o vlastním kódu.
*   **`WebSearchTool`:** Dává agentovi schopnost provádět vyhledávání Google pro přístup k informacím v reálném čase z internetu. Jedná se o klíčový nástroj pro výzkum a udržování aktuálních informací.
*   **`JulesAPITool`:** Integrace s Jules API od Google pro AI-asistované programování. Funkce zahrnují:
    *   Vytváření a správu coding sessions
    *   Výpis dostupných GitHub repozitářů
    *   Monitorování průběhu sessions a aktivit
    *   Posílání dalších instrukcí do aktivních sessions
    *   Plná Pydantic v2 validace dat pro type safety
    *   Bezpečná správa API klíčů přes proměnné prostředí

### 2.3. `SharedContext` (`core/context.py`)

*   **Odpovědnost:** Datová sběrnice a "životodárná síla" systému.
1.  Je to `dataclass`, jejíž instance je předána každému pluginu v každém cyklu.
2.  Obsahuje celý stav pro aktuální cyklus, včetně `session_id`, `current_state`, `user_input`, `history`, flexibilního `payload` pro sdílení dat mezi pluginy a **specifického loggeru pro danou session**.
*   **Struktura (`dataclass`):**
    *   `session_id: str`: Jedinečné ID pro aktuální session.
    *   `current_state: str`: Aktuální stav hlavní smyčky (`LISTENING`, `THINKING` atd.).
    *   `user_input: str | None`: Poslední vstup od uživatele.
    *   `history: list`: Krátkodobá historie aktuální konverzace.
    *   `payload: dict`: "Nákladový prostor" pro data předávaná mezi pluginy.
    *   `logger: logging.Logger`: Nakonfigurovaný logger, který automaticky vkládá `session_id` do všech záznamů, což zajišťuje jasné a kontextuální protokolování napříč všemi pluginy.
