# 🗺️ Roadmap Projektu: Z Nomada k Sophii

Tento dokument definuje strategickou vizi a fázovaný plán pro budoucí vývoj projektu. Cílem je postupně integrovat pokročilé kognitivní funkce a koncepty z původní architektury (nyní archivované ve složce `integrace/`) do nového, stabilního a robustního jádra **Nomad**.

## Hlavní Vize

Naší konečnou vizí je stvoření **Artificial Mindful Intelligence (AMI)**. Jádro Nomad představuje spolehlivý exekuční a interaktivní základ. Následující fáze se zaměří na jeho obohacení o schopnost učení, sebereflexe a autonomního rozhodování, čímž ho transformujeme zpět v plnohodnotnou Sophii.

## Architektura Cílového Stavu

Cílem je vytvořit systém, který implementuje **Hierarchickou Kognitivní Architekturu (HKA)**, kde se každý příchozí úkol zpracovává postupně přes tři vrstvy:

1.  **Reptiliánský mozek (Nomad Core):** Okamžitá, reflexivní reakce. Dokáže systém vykonat úkol přímo pomocí jednoho nástroje?
2.  **Savčí mozek (Context Server):** Rychlá, kontextová reakce. Už jsme řešili podobný úkol? Můžeme použít řešení z paměti?
3.  **Neokortex (Planner & Agent Team):** Pomalé, deliberativní plánování. Pro komplexní úkoly, které vyžadují sestavení nového plánu a spolupráci více agentů.

Tento dokument popisuje cestu, jak se k tomuto cíli dostat.

---

## Fáze 1: Posílení a Stabilizace Jádra Nomad (Hardening)

Než začneme přidávat komplexní funkce, musíme zajistit, že náš základ je stoprocentně spolehlivý.

-   **[ ] Komplexní Testovací Sada:**
    -   Vytvořit jednotkové a integrační testy pro všechny klíčové komponenty: `JulesOrchestrator`, `MCPClient` a všechny `MCP Servery`.
    -   Implementovat mockování pro LLM API, aby testy mohly běžet offline a byly deterministické.
    -   Nastavit CI/CD pipeline (např. GitHub Actions) pro automatické spouštění testů.
-   **[ ] Konfigurační Management:**
    -   Zlepšit správu konfigurace (např. porty pro MCP servery) tak, aby byla snadno modifikovatelná přes `config.yaml` a nebyla pevně zakódovaná.
-   **[ ] Zlepšení Spolehlivosti `start.sh`:**
    -   Přidat robustnější kontrolu, zda se MCP servery skutečně spustily, než se spustí TUI (např. pomocí `netcat` nebo podobného nástroje pro kontrolu otevřených portů).

**Definition of Done:**
-   Testovací pokrytí jádra dosahuje >90 %.
-   Všechny klíčové parametry jsou konfigurovatelné.
-   Spouštěcí skript je plně spolehlivý.

---

## Fáze 2: Integrace Pokročilé Paměti

Současný `MemoryManager` je jednoduchý. V této fázi integrujeme pokročilé paměťové koncepty z původní architektury.

-   **[ ] Znovuzavedení `PostgreSQL` a `Redis`:**
    -   Nahradit `SQLite` za `PostgreSQL` pro ukládání dlouhodobých a strukturovaných vzpomínek.
    -   Implementovat `Redis` jako rychlou cache pro krátkodobou paměť.
-   **[ ] Vytvoření `Memory MCP Server`:**
    -   Přepsat `memory_server.py`, aby poskytoval komplexní rozhraní pro práci s pamětí (ukládání, vyhledávání, asociace, zapomínání).

**Definition of Done:**
-   Agent ukládá a načítá historii a vzpomínky z PostgreSQL a Redis přes dedikovaný MCP server.

---

## Fáze 3: Implementace Kognitivní Triage a Savčí Vrstvy

V této fázi začneme budovat skutečnou kognitivní architekturu.

-   **[ ] `Ethos MCP Server`:**
    -   Vytvořit server, který bude poskytovat etické zhodnocení plánů na základě principů v `DNA.md`.
-   **[ ] `Context MCP Server` (Savčí mozek):**
    -   Vytvořit server, který na základě promptu prohledá paměť a najde relevantní minulé zkušenosti.
    -   Dokáže navrhnout rychlé řešení, pokud existuje silná shoda s minulým úspěšným úkolem.
-   **[ ] Evoluce Orchestrátoru na "Triage System":**
    -   Upravit `JulesOrchestrator` tak, aby implementoval kognitivní tok:
        1.  Zkusí úkol vyřešit přímo (Reptiliánská vrstva - již existuje).
        2.  Pokud to nejde, zeptá se `Context Serveru` (Savčí vrstva).
        3.  Pokud ani to nestačí, předá úkol k plnému naplánování (Neokortex - viz Fáze 4).

**Definition of Done:**
-   Orchestrátor je schopen řešit jednoduché úkoly pomocí kontextu z paměti, aniž by musel volat LLM pro plné plánování.
-   Všechny plány jsou před exekucí validovány přes `Ethos Server`.

---

## Fáze 4: Obnova Ekosystému Specializovaných Agentů (Neokortex)

V této fázi obnovíme koncept specializovaných agentů pro řešení komplexních úkolů.

-   **[ ] `Planner MCP Server`:**
    -   Vytvořit server zodpovědný za dekompozici komplexních cílů na menší, proveditelné kroky.
-   **[ ] Zavedení Meta-Orchestrátoru (nebo rozšíření stávajícího):**
    -   Vytvořit vyšší řídící vrstvu, která bude sestavovat "týmy" agentů (`Planner`, `Engineer`, `Tester`) a řídit jejich spolupráci na základě plánu z `Planner Serveru`.
-   **[ ] Reimplementace Agentů:**
    -   Přepsat agenty z `integrace/agents/` tak, aby fungovali v nové MCP architektuře.

**Definition of Done:**
-   Systém je schopen přijmout komplexní úkol, vytvořit pro něj podrobný plán a delegovat jeho exekuci na tým specializovaných agentů.

---

## Fáze 5: Dosažení Autonomie (Self-Improvement Loop)

Cílem této finální fáze je propojit všechny předchozí kroky a vytvořit systém, který se dokáže sám zlepšovat.

-   **[ ] Implementace "Spánkového Cyklu":**
    -   Po dokončení úkolu nebo v době nečinnosti se agent přepne do "spánkového" režimu, kde analyzuje své předchozí akce a identifikuje příležitosti k vylepšení.
-   **[ ] Schopnost Sebe-Modifikace:**
    -   Agent bude schopen na základě svých zjištění vytvářet nové nástroje, upravovat své prompty nebo navrhovat změny ve své vlastní architektuře a vytvářet pull requesty k revizi.

**Definition of Done:**
-   Agent je schopen samostatně identifikovat neefektivitu ve svém postupu a navrhnout konkrétní, implementovatelnou změnu ve svém kódu nebo konfiguraci.

Tento roadmap představuje dlouhodobou vizi. Úspěšným dokončením těchto kroků se přiblížíme našemu konečnému cíli: stvoření skutečné Artificial Mindful Intelligence.