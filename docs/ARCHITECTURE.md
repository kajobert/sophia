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

### 2. ConversationalManager
- **Soubor:** `core/conversational_manager.py`
- **Popis:** Je to nový nejvyšší řídící prvek agenta, který funguje jako "osvícený manažer". Jeho zodpovědnosti jsou:
    - Vedení konverzace s uživatelem.
    - Použití LLM k primárnímu rozhodnutí na základě vstupu: má se jednat o dotaz na stav, nebo o komplexní úkol?
    - Volání svých interních metod (např. `_get_worker_status`) pro jednoduché dotazy.
    - Delegování komplexních úkolů na `WorkerOrchestrator`.
    - Formulování finální, srozumitelné odpovědi pro uživatele na základě výsledků.

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