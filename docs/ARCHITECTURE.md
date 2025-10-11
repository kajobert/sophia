# Architektura: Nomad Core (Manager/Worker)

Tento dokument popisuje aktuální technickou architekturu projektu, která vznikla po rozsáhlém refaktoringu. Nové jádro, postavené na architektuře **Manager/Worker**, je navrženo pro robustnost, modularitu a oddělení zodpovědností.

## Klíčové principy

Architektura je postavena na několika klíčových principech:
1.  **Oddělení zodpovědností:** Konverzační logika (Manager) je striktně oddělena od logiky pro provádění úkolů (Worker).
2.  **Asynchronní zpracování:** Všechny operace jsou navrženy jako asynchronní, aby se zabránilo blokování a zajistila se plynulost uživatelského rozhraní.
3.  **Modularita nástrojů:** Nástroje, které Worker používá, jsou izolovány v samostatných serverových procesech, což umožňuje jejich snadnou správu a rozšiřování.

## Hlavní komponenty

Následující diagram znázorňuje tok informací mezi hlavními komponentami systému:

```
+------------------+      (1) Uživ. vstup      +---------------------------+      (3) Delegování úkolu      +-----------------------+
|                  | ------------------------> |                           | -------------------------> |                       |
|  TUI (app.py)    |                           |  ConversationalManager    |                            |  WorkerOrchestrator   |
|                  |      (2) Zobrazení        |  (core/conversational...) |                            | (core/orchestrator)   |
|                  | <------------------------ |                           | <------------------------- |                       |
+------------------+      (zprávy)             +-------------+-------------+      (4) Výsledek úkolu      +-----------+-----------+
                                                            |                                            |
                                                            | (LLM pro rozhodnutí)                       | (LLM pro kroky)
                                                            |                                            |
                                                            v                                            v
                                                    +----------------------+                 +---------------------+
                                                    |                      |                 |                     |
                                                    |   Gemini API / LLM   |                 |     MCP Servery     |
                                                    |                      | <---------------> | (mcp_servers/worker)|
                                                    +----------------------+                 +---------------------+
```

### 1. Textual User Interface (TUI)
- **Soubor:** `tui/app.py`
- **Technologie:** [Textual](https://textual.textualize.io/)
- **Popis:** TUI je hlavním vstupním bodem aplikace.
    - Vytváří a spravuje grafické rozhraní v terminálu.
    - Přijímá vstupy od uživatele a předává je `ConversationalManageru`.
    - Spouští `ConversationalManager` v asynchronním "workeru", aby se neblokovalo UI.
    - Zpracovává zprávy od `RichPrinter` a zobrazuje je v příslušných widgetech.

### 2. ConversationalManager (Agile Project Manager)
- **Soubor:** `core/conversational_manager.py`
- **Popis:** Povýšen na roli "Agilního Projektového Manažera". Již nedeleguje pouze velké úkoly, ale aktivně řídí celý životní cyklus projektu.
    - **Triage:** Nejprve analyzuje požadavek uživatele, aby určil, zda jde o jednoduchý, přímo řešitelný úkol, nebo o komplexní projekt.
    - **Projektové Řízení:** U komplexních úkolů:
        1. Vytvoří hlavní cíl v `PlanningServeru`.
        2. Rozdělí práci na počáteční dílčí úkol (např. "naplánuj kroky").
        3. Vstupuje do smyčky, kde postupně bere další proveditelný úkol z plánu.
        4. Každý dílčí úkol deleguje na `WorkerOrchestrator`.
        5. Aktualizuje stav úkolu (dokončeno, selhalo) v `PlanningServeru`.
    - **Resilientní Zpracování Chyb:** Pokud Worker selže, `ConversationalManager` se nevzdá.
        1. Zavolá `ReflectionServer`, aby analyzoval historii neúspěšného úkolu.
        2. Prezentuje uživateli shrnutí chyby a výsledek reflexe.
        3. Požádá o další instrukce, čímž efektivně zapojuje uživatele do řešení problémů.
    - **Učení se z Projektů:** Po úspěšném dokončení celého projektu spustí finální sebereflexi nad celou historií projektu, aby se poučil pro příště.

### 3. WorkerOrchestrator
- **Soubor:** `core/orchestrator.py`
- **Popis:** Je to "pracant" systému, který vykonává delegované úkoly.
    - Pracuje v rámci "rozpočtu na složitost" (definovaný počet kroků), aby se zabránilo zacyklení u jednoduchých úkolů.
    - Udržuje si vlastní kontext a historii pro řešení daného úkolu.
    - Komunikuje s LLM pro sekvenční provádění jednotlivých kroků vedoucích ke splnění úkolu.
    - Volá nástroje z profilu `worker` prostřednictvím `MCPClient`.
    - Vrací finální výsledek (např. `completed`, `needs_planning`) zpět `ConversationalManageru`.

### 4. MCP (Modular Component Protocol) Servery
- **Složka:** `mcp_servers/worker/`
- **Popis:** Každý soubor `*_server.py` v této složce představuje samostatný, na pozadí běžící proces, který poskytuje sadu souvisejících nástrojů.
- **Komunikace:** `WorkerOrchestrator` s nimi komunikuje přes `MCPClient` pomocí jednoduchého JSON-RPC protokolu.
- **Profily:** Architektura podporuje profily (`worker`, `manager`). V současné implementaci jsou všechny nástroje pro provádění práce v profilu `worker`.

### 5. RichPrinter
- **Soubor:** `core/rich_printer.py`
- **Popis:** Funguje jako prostředník mezi logikou aplikace a jejím zobrazením. Místo přímého tisku do konzole emituje strukturované zprávy (`LogMessage`, `ChatMessage`), které TUI zachytává a zobrazuje.

### 6. MemoryManager
- **Soubor:** `core/memory_manager.py`
- **Technologie:** SQLite
- **Popis:** Zajišťuje perzistenci dat. Ukládá kompletní historii konverzace pro každé sezení, což umožňuje navázat na přerušenou práci.

---

## Archivovaná architektura

Původní kód staré architektury (založené na FastAPI, kognitivních vrstvách a agentech) byl přesunut do složky `integrace/`. Slouží jako archiv a zdroj inspirace pro budoucí integraci pokročilých funkcí do jádra Nomad.