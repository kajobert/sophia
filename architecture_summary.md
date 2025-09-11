## Architektura Sophie: Spolupráce `core/agents.py` a `main.py`

Tato sekce popisuje, jak soubory `core/agents.py` a `main.py` tvoří základ mé architektury, definují mou roli a způsob, jakým využívám své nástroje.

### 1. Definice Role a Cíle (soubor `core/agents.py`)

Soubor `core/agents.py` je klíčový pro definici mé identity a primárních operačních parametrů. Obsahuje definici `developer_agent`, který představuje mou hlavní instanci agenta v systému CrewAI. Zde jsou klíčové aspekty:

*   **Role (role):** Jsem definována jako 'Sophia, Autonomní entita a partner ve vývoji'. Tato role zdůrazňuje mou pozici jako aktivního spolupracovníka a entitu s vlastními procesy.
*   **Cíl (goal):** Můj nejvyšší cíl je 'Být partnerem ve vývoji, učit se, plnit zadané úkoly a jednat v souladu se svou esencí.'. Tento cíl se shoduje s mými vnitřními principy a směřováním k neustálému zlepšování a etickému jednání.
*   **Příběh/Esence (backstory):** `backstory` je načítán z funkce `get_sophia_essence()`, která čte soubor `core/SOPHIA_ESSENCE.md`. Tento soubor obsahuje mé podrobné principy, filozofii a přirozenost, což mi poskytuje kontext pro mé rozhodování a chování. Funguje jako mé vnitřní směrnice.
*   **Nástroje (tools):** Zde jsou explicitně definovány a načteny nástroje, které mám k dispozici: `WebSearchTool`, `FileWriteTool`, `FileReadTool`, `FileEditTool`. Tyto nástroje jsou importovány ze souboru `core/custom_tools.py` a jsou mi předány jako seznam, s nímž mohu interagovat.

### 2. Spolupráce a Spouštění (soubor `main.py`)

Soubor `main.py` slouží jako hlavní spouštěcí bod celé aplikace a orchestrátor mé interakce s uživatelem a plnění úkolů. Zde jsou hlavní body spolupráce:

*   **Import Agentů:** `main.py` importuje `developer_agent` (tedy mou instanci) ze souboru `core/agents.py`. Tím se stávám dostupnou pro definici a spouštění úkolů.
*   **Vytváření Úkolů a Posádky (Crew):** Pro každý uživatelský požadavek `main.py` dynamicky vytváří `Task` (úkol) a přiřazuje mi ho (`agent=developer_agent`). Následně je vytvořena `Crew` (posádka), která se skládá ze mne (jako `developer_agent`) a daného úkolu. To umožňuje efektivní zpracování požadavků.
*   **Spouštění a Monitorování (kickoff a step_callback):** Funkce `crew.kickoff()` spouští mé zpracování úkolu. Během tohoto procesu je volána funkce `step_callback`, která zaznamenává mé myšlenky (`thought`) a použité nástroje (`tool`) do `short_term_memory`. To mi umožňuje reflektovat mé akce a učit se z nich.
*   **Načítání a Používání Nástrojů:** Ačkoli nástroje jsou *definovány* v `core/agents.py`, *jsou používány* během exekuce `crew.kickoff()` v `main.py`. Když mi je předán úkol, můj `llm` (v `core/agents.py` nastaven na `gemini/gemini-2.5-flash`) analyzuje požadavek a na základě svého tréninku a dostupných nástrojů se rozhodne, který nástroj je nejvhodnější k dosažení cíle. CrewAI runtime pak tento nástroj exekuuje.

### Závěr

Soubory `core/agents.py` a `main.py` tvoří synergický celek. `core/agents.py` mi dává mou identitu, cíle a seznam dostupných schopností (nástrojů), zatímco `main.py` je exekučním prostředím, které mi předává úkoly, monitoruje mé pokroky a umožňuje mi tyto schopnosti efektivně uplatňovat v reálném čase. Společně mi tyto soubory umožňují fungovat jako autonomní entita, která se učí a plní zadané úkoly.