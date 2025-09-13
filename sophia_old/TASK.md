# ZADÁNÍ: Architektonický Přechod na Sophia V2.0

## CÍL
Provést kompletní refaktoring a rozšíření architektury Sophie na verzi 2.0. Cílem je vytvořit robustní, odolný a skutečně autonomní multi-agentní systém s pokročilou pamětí a schopností sebe-rozvoje, připravený pro webovou interakci.

## KONTEXT
Současná architektura s jedním agentem a "berličkou" v podobě `DecisionTool` narazila na své limity. Potřebujeme přejít na systém, kde rozhodování nevzniká z pevně daných pravidel, ale z dynamické spolupráce specializovaných agentů. Tímto refaktoringem položíme základy pro skutečnou, škálovatelnou autonomii.

## PLÁN IMPLEMENTACE

### Fáze 1: Refaktoring Nástrojů a Konsolidace Jádra

Cílem je vyčistit kód a připravit ho na novou architekturu.

1.  **Sjednoť Nástroje:**
    * V souboru `core/custom_tools.py` převeď všechny volně stojící funkce (`directory_listing_tool`, `directory_creation_tool`, `memory_inspection_tool` atd.) do formátu tříd, které dědí z `langchain_core.tools.BaseTool`.
    * **DŮLEŽITÉ:** Všechny importy `BaseTool` musí být opraveny na `from langchain_core.tools import BaseTool`, aby se předešlo chybám s novými verzemi knihoven.
2.  **Odstraň `DecisionTool`:**
    * Ze souboru `core/custom_tools.py` kompletně odstraň kód pro `DecisionTool`.
    * V souboru `core/agents.py` odstraň `DecisionTool` ze seznamu nástrojů `developer_agent`.
3.  **Vrať Nástroje Vývojáři:**
    * Do seznamu nástrojů `developer_agent` v `core/agents.py` dočasně přidej všechny sjednocené nástroje z `custom_tools.py` (včetně `FileWriteTool`, `FileEditTool`, `DirectoryListingTool`, `DirectoryCreationTool`, `MemoryInspectionTool` atd.). Tím mu dáme plnou moc pro další kroky, než role převezmou noví agenti.

---

### Fáze 2: Implementace Pokročilé Paměti (V2.1)

Vytvoříme robustní paměťové jádro.

1.  **Strukturovaná Epizodická Paměť:**
    * Vytvoř nový soubor `memory/episodic_memory.py`.
    * V něm implementuj třídu `EpisodicMemory`, která bude používat **SQLite databázi** (`memory/episodic_log.sqlite`).
    * Bude mít metodu `add_event(agent_name, action, input, output, status)`, která zapíše každý krok jakéhokoliv agenta do databáze.
    * Uprav `main.py` a `step_callback`, aby používaly tuto novou třídu místo starého textového logu.
2.  **Měření Spotřeby Tokenů:**
    * Vytvoř nový soubor `core/token_counter_tool.py`.
    * V něm implementuj `TokenCounterTool` (jako třídu dědící z `BaseTool`), který pomocí knihovny `tiktoken` spočítá počet tokenů v zadaném textu.
    * Uprav `main.py` tak, aby po každé interakci zavolal tento nástroj na vstup i výstup a zapsal výsledek (`timestamp, input_tokens, output_tokens, total_tokens`) do nového souboru `logs/token_usage.log`.

---

### Fáze 3: Implementace Imunitního Systému (Guardian Protocol)

Zajistíme, aby se Sophia nikdy nenávratně nerozbila.

1.  **Vytvoř `guardian.py`:**
    * V kořenovém adresáři projektu vytvoř nový, samostatný skript `guardian.py`.
    * Tento skript bude v nekonečné smyčce spouštět `main.py` jako podproces.
    * Bude monitorovat návratový kód podprocesu. Pokud `main.py` skončí s chybou (nenulový kód), Guardian provede záchrannou operaci.
2.  **Implementuj Automatický Rollback:**
    * V `guardian.py`, v případě detekce pádu, přidej logiku, která:
        1.  Spustí příkaz `git reset --hard HEAD` k vrácení všech souborů do stavu posledního committu.
        2.  Zapíše čas a chybovou hlášku do souboru `SOS.log`.
        3.  Znovu se pokusí spustit `main.py`.

---

### Fáze 4: Vývoj Multi-agentního Jádra

Přestavíme mozek Sophie.

1.  **Definuj Nové Agenty:**
    * V souboru `core/agents.py` vytvoř definice pro nové, specializované agenty:
        * **`planning_agent`:** Jeho `goal` bude analyzovat komplexní cíle a rozbíjet je na menší, proveditelné úkoly. Bude mít k dispozici nástroje pro čtení souborů a výpis adresářů.
        * **`archivist_agent`:** Vylepšený `memory_agent`. Jeho jediným nástrojem bude `LtmWriteTool` a nástroj pro čtení z nové epizodické SQLite databáze.
2.  **Uprav `main.py` pro Delegaci:**
    * Přepracuj hlavní smyčku v `main.py`. Nový `user_input` už nebude rovnou předán `developer_agentovi`.
    * Místo toho se vytvoří `Task` pro `planning_agent`, jehož cílem bude vytvořit plán.
    * Následně se spustí nová `Crew` s celým týmem agentů, kteří si budou úkoly delegovat (bude potřeba nastavit `allow_delegation=True` u Plánovače).

## OČEKÁVANÝ VÝSLEDEK
Plně refaktorovaný a rozšířený projekt Sophia V2.0. Systém bude odolný proti chybám, bude mít pokročilou a strukturovanou paměť, bude schopen monitorovat svou vlastní spotřebu a jeho jádro bude tvořeno spolupracujícím týmem specializovaných agentů, připravených na implementaci webového rozhraní a další komplexní úkoly.