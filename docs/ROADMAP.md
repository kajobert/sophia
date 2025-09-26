# 🗺️ Roadmap Projektu: Z Nomada k Sophii

Tento dokument definuje strategickou vizi a fázovaný plán pro budoucí vývoj projektu. Cílem je postupně integrovat pokročilé kognitivní funkce a koncepty z původní architektury (nyní archivované ve složce `integrace/`) do nového, stabilního a robustního jádra **Nomad**.

## Hlavní Vize

Naší konečnou vizí je stvoření **Artificial Mindful Intelligence (AMI)**. Jádro Nomad představuje spolehlivý exekuční a interaktivní základ. Následující fáze se zaměří na jeho obohacení o schopnost učení, sebereflexe a autonomního rozhodování, čímž ho transformujeme zpět v plnohodnotnou Sophii.

---

## Fáze 1: Posílení a Stabilizace Jádra Nomad (Hardening)

Než začneme přidávat komplexní funkce, musíme zajistit, že náš základ je stoprocentně spolehlivý.

-   **[ ] Komplexní Testovací Sada:**
    -   Vytvořit jednotkové a integrační testy pro všechny klíčové komponenty: `JulesOrchestrator`, `MCPClient` a všechny `MCP Servery`.
    -   Implementovat mockování pro LLM API, aby testy mohly běžet offline a byly deterministické.
    -   Nastavit CI/CD pipeline (např. GitHub Actions) pro automatické spouštění testů při každém pushi.

-   **[ ] Konfigurační Management:**
    -   Zlepšit správu konfigurace (např. porty pro MCP servery) tak, aby byla snadno modifikovatelná přes `config.yaml` a nebyla pevně zakódovaná.

-   **[ ] Zlepšení Spolehlivosti `start.sh`:**
    -   Přidat robustnější kontrolu, zda se MCP servery skutečně spustily, než se spustí TUI (např. pomocí `netcat` nebo podobného nástroje pro kontrolu otevřených portů).

---

## Fáze 2: Integrace Pokročilé Paměti

Současný `MemoryManager` je jednoduchý. V této fázi integrujeme pokročilé paměťové koncepty z původní architektury.

-   **[ ] Znovuzavedení `PostgreSQL` a `Redis`:**
    -   Nahradit `SQLite` za `PostgreSQL` pro ukládání dlouhodobých a strukturovaných vzpomínek (historie, plány, znalosti).
    -   Implementovat `Redis` jako rychlou cache pro krátkodobou paměť a meziprocesovou komunikaci.
    -   Inspirace: `integrace/memory/advanced_memory.py`.

-   **[ ] Vytvoření `Memory MCP Server`:**
    -   Přepsat `memory_server.py` tak, aby poskytoval komplexní rozhraní pro práci s pamětí (ukládání, vyhledávání, asociace, zapomínání).
    -   Agent bude s pamětí komunikovat výhradně přes tento server.

---

## Fáze 3: Kognitivní Funkce jako MCP Servery

Klíčové kognitivní funkce z původní architektury budou reimplementovány jako specializované, samostatné MCP servery. Tím zachováme modularitu a oddělení zodpovědností.

-   **[ ] `Ethos MCP Server`:**
    -   Vytvořit server, který bude poskytovat etické zhodnocení plánů a akcí.
    -   Orchestrátor mu předloží plán a `Ethos Server` vrátí skóre nebo doporučení na základě principů v `DNA.md`.
    -   Inspirace: `integrace/core/ethos_module.py`.

-   **[ ] `Planner MCP Server`:**
    -   Vytvořit server zodpovědný za dekompozici komplexních úkolů na menší, proveditelné kroky.
    -   Tento server převezme zodpovědnost za "plánování", kterou má nyní implicitně LLM v orchestrátoru.

---

## Fáze 4: Obnova Ekosystému Specializovaných Agentů

V této fázi obnovíme koncept specializovaných agentů, kteří budou spolupracovat na řešení úkolů.

-   **[ ] Zavedení Meta-Orchestrátoru:**
    -   Vytvořit novou, vyšší řídící vrstvu, která bude přijímat komplexní cíle.
    -   Tento meta-orchestrátor úkol rozdělí a sestaví "tým" agentů (např. `Planner`, `Engineer`, `Tester`) k jeho vyřešení.
    -   `JulesOrchestrator` (současný orchestrátor) se stane jedním z nástrojů, které bude tento meta-orchestrátor používat pro exekuci jednotlivých kroků.

-   **[ ] Reimplementace Agentů:**
    -   Přepsat agenty z `integrace/agents/` tak, aby fungovali v nové architektuře a komunikovali přes MCP servery.

---

## Fáze 5: Dosažení Autonomie (Self-Improvement Loop)

Cílem této finální fáze je propojit všechny předchozí kroky a vytvořit systém, který se dokáže sám zlepšovat.

-   **[ ] Implementace "Spánkového Cyklu":**
    -   Po dokončení úkolu nebo v době nečinnosti se agent přepne do "spánkového" režimu.
    -   V tomto režimu analyzuje své předchozí akce, vyhodnocuje úspěšnost, identifikuje chyby a navrhuje vylepšení svého vlastního kódu nebo promptů.

-   **[ ] Schopnost Sebe-Modifikace:**
    -   Agent bude schopen na základě svých zjištění ve spánkovém cyklu vytvářet nové nástroje, upravovat své prompty nebo dokonce navrhovat změny ve své vlastní architektuře a vytvářet pull requesty k revizi.

Tento roadmap představuje dlouhodobou vizi. Každá fáze bude vyžadovat pečlivé plánování, implementaci a testování. Úspěšným dokončením těchto kroků se přiblížíme našemu konečnému cíli: stvoření skutečné Artificial Mindful Intelligence.