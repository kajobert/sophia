# Architektura: Nomad Core

Tento dokument popisuje aktuální technickou architekturu projektu, která vznikla po rozsáhlém refaktoringu. Nové jádro, s kódovým označením **Nomad**, je navrženo pro robustnost, modularitu a interaktivní použití přes terminálové rozhraní (TUI).

## Klíčové principy

Architektura je postavena na několika klíčových principech:
1.  **Oddělení zodpovědností:** Každá klíčová funkce (uživatelské rozhraní, řízení agenta, vykonávání nástrojů) je zapouzdřena ve vlastní komponentě.
2.  **Asynchronní zpracování:** Všechny operace jsou navrženy jako asynchronní, aby se zabránilo blokování a zajistila se plynulost uživatelského rozhraní.
3.  **Modularita nástrojů:** Nástroje, které agent používá, jsou izolovány v samostatných serverových procesech, což umožňuje jejich snadnou správu, rozšiřování a restartování.

## Hlavní komponenty

Následující diagram znázorňuje tok informací mezi hlavními komponentami systému:

```
+------------------+      (1) Uživ. vstup      +----------------------+      (3) Spuštění      +---------------------+
|                  | ------------------------> |                      | -------------------> |                     |
|  TUI (app.py)    |                           |  JulesOrchestrator   |                      |     MCP Servery     |
|  (Textual)       |      (2) Zobrazení        |  (core/orchestrator) | <------------------+ | (mcp_servers/*.py)  |
|                  | <------------------------ |                      |      (4) Výsledek    |                     |
+------------------+      (zprávy)             +----------+-----------+                      +---------------------+
        ^                                                  |
        | (zprávy)                                         | (2) Volání LLM
        |                                                  |
+-------+----------+                                       v
|                  |                               +----------------------+
|   RichPrinter    |                               |                      |
| (core/printer)   | ----------------------------> |   Gemini API / LLM   |
|                  |      (1) Logování             |                      |
+------------------+                               +----------------------+

```

### 1. Textual User Interface (TUI)
- **Soubor:** `tui/app.py`
- **Technologie:** [Textual](https://textual.textualize.io/)
- **Popis:** TUI je hlavním vstupním bodem celé aplikace a nahrazuje původní `interactive_session.py`. Je zodpovědná za:
    - Vytvoření a správu grafického rozhraní v terminálu (chatovací okno, logy, vstupní pole).
    - Přijímání vstupů od uživatele.
    - Spouštění `JulesOrchestrator` v asynchronním "workeru", aby se neblokovalo UI.
    - Zpracovávání zpráv od `RichPrinter` a jejich zobrazování v příslušných widgetech.

### 2. JulesOrchestrator
- **Soubor:** `core/orchestrator.py`
- **Popis:** Je to mozek celého agenta. Jeho zodpovědnosti jsou:
    - Udržování kontextu a historie konverzace pro dané sezení (`session_id`).
    - Komunikace s LLM (sestavování promptů, odesílání požadavků).
    - Parsování odpovědí od LLM a rozhodování, který nástroj zavolat.
    - Volání nástrojů prostřednictvím `MCPClient`.
    - Využívání `RichPrinter` pro odesílání informací o svém stavu a výsledcích do TUI.

### 3. MCP (Modular Component Protocol) Servery
- **Složka:** `mcp_servers/`
- **Popis:** Každý soubor `*_server.py` představuje samostatný, na pozadí běžící proces, který poskytuje sadu souvisejících nástrojů. Například `file_system_server.py` obsahuje nástroje pro čtení a zápis souborů.
- **Komunikace:** Orchestrátor s nimi komunikuje přes `MCPClient` pomocí jednoduchého JSON-RPC protokolu přes standardní vstup/výstup.
- **Výhody:** Tato architektura umožňuje restartovat jednotlivé sady nástrojů (např. po vytvoření nového nástroje) bez nutnosti restartu celé aplikace.

### 4. RichPrinter
- **Soubor:** `core/rich_printer.py`
- **Popis:** Funguje jako prostředník mezi logikou aplikace a jejím zobrazením. Místo přímého tisku do konzole emituje strukturované zprávy (`LogMessage`, `ChatMessage`).
- **Integrace s TUI:** V TUI režimu jsou tyto zprávy zachyceny a zobrazeny v příslušných widgetech. Pokud aplikace běží bez TUI, zprávy jsou ignorovány, ale logování do souboru stále funguje.

### 5. MemoryManager
- **Soubor:** `core/memory_manager.py`
- **Technologie:** SQLite
- **Popis:** Zajišťuje perzistenci dat. Ukládá kompletní historii konverzace pro každé sezení, což umožňuje navázat na přerušenou práci.

---

## Archivovaná architektura

Původní kód staré architektury (založené na FastAPI, kognitivních vrstvách a agentech) byl přesunut do složky `integrace/`. Slouží jako archiv a zdroj inspirace pro budoucí integraci pokročilých funkcí do jádra Nomad.