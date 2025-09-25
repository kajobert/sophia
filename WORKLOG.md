# Pracovní Deník (Worklog) Projektu Sophia

Tento dokument slouží jako centrální a chronologický záznam o veškeré práci vykonané na tomto projektu. Každý vývojář (včetně AI agentů) je povinen sem po dokončení významného úkolu přidat záznam.

## Formát Záznamu

Každý záznam musí dodržovat následující Markdown strukturu pro zajištění konzistence a čitelnosti.

```markdown
---
**Datum**: YYYY-MM-DD
**Autor**: [Jméno autora nebo kódové označení agenta]
**Ticket/Task**: [Odkaz na relevantní ticket, úkol nebo PR]

### Téma: Stručný a výstižný název vykonané práce.

**Popis Práce:**
- Detailní popis toho, co bylo uděláno.
- Jaké soubory byly změněny, vytvořeny nebo smazány.
- Klíčová rozhodnutí, která byla učiněna.

**Důvod a Kontext:**
- Proč byla tato změna nutná?
- Jaký problém řeší nebo jakou hodnotu přináší?
- Jaké alternativy byly zvažovány a proč byly zamítnuty?

**Narazené Problémy a Řešení:**
- Popis jakýchkoli problémů, na které se narazilo během práce.
- Jak byly tyto problémy vyřešeny? (Toto je klíčové pro budoucí učení).

**Dopad na Projekt:**
- Jak tato změna ovlivňuje zbytek projektu?
- Jsou zde nějaké návazné kroky, které je třeba udělat?
- Co by měli ostatní vývojáři vědět?
---
```

---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Zavedení nových principů spolupráce.

### Téma: Založení WORKLOG.md a formalizace nových pravidel.

**Popis Práce:**
- Vytvořil jsem tento soubor (`WORKLOG.md`) jako centrální deník projektu.
- Definoval jsem standardizovaný formát pro všechny budoucí záznamy.
- Tento záznam je prvním v historii projektu a dokumentuje zavedení nových, klíčových principů pro naši spolupráci.

**Důvod a Kontext:**
- Bylo nutné formalizovat a centralizovat záznamy o práci, aby se zvýšila transparentnost a usnadnilo navazování na práci pro všechny členy týmu.
- Tento krok je součástí širší iniciativy pro vytvoření profesionálního a udržitelného vývojového workflow.

**Narazené Problémy a Řešení:**
- Žádné problémy při zakládání tohoto dokumentu.

**Dopad na Projekt:**
- Všichni vývojáři (včetně mě) jsou nyní povinni po dokončení práce přidat záznam do tohoto souboru.
- Zvyšuje se tím dohledatelnost a sdílení znalostí v rámci projektu.
---
---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Inicializace Projektu Sophia (Replikace Agenta Jules)

### Téma: Fáze 1 - Vytvoření základní struktury a konfigurace projektu.

**Popis Práce:**
- Vytvořen hlavní adresář projektu `sophia_jules_replica/`.
- Vytvořena kompletní podadresářová struktura (`core/`, `tools/`, `memory/`, `config/`).
- Vytvořen soubor se závislostmi `requirements.in` s `google-generativeai`, `python-dotenv`, `PyYAML`.
- Vytvořeny konfigurační soubory:
    - `config/config.yaml` se základní strukturou pro model a cesty.
    - `.env.example` jako šablona pro API klíč.
    - `.gitignore` pro ignorování dočasných a citlivých souborů.
- Zkopírovány a přejmenovány paměťové soubory `agent.md` -> `memory/JULES.md` a `AGENTS.md` -> `memory/AGENTS.md`.

**Důvod a Kontext:**
- Tento krok představuje implementaci Fáze 1 z technického plánu `PLAN_JULES_REPLICA.md`.
- Cílem bylo vytvořit pevný a škálovatelný základ pro budoucí vývoj agenta "Jules Replica" v rámci projektu Sophia.
- Tímto je splněn počáteční úkol "Aktivuj Projekt Sanctuary a rozbal Genesis archiv" v jeho plné, technické podobě.

**Narazené Problémy a Řešení:**
- Žádné významné problémy se nevyskytly. Proces proběhl podle plánu.

**Dopad na Projekt:**
- Projekt má nyní připravenou základní strukturu.
- Dalším krokem bude implementace Fáze 2: Jádro Orchestrátoru.
- Všechny budoucí práce budou stavět na tomto základě.
---
---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Implementace Jádra Orchestrátoru (Fáze 2)

### Téma: Fáze 2 - Implementace třídy JulesOrchestrator.

**Popis Práce:**
- Vytvořen soubor `sophia_jules_replica/core/orchestrator.py` s kostrou třídy `JulesOrchestrator`.
- Vytvořen soubor `sophia_jules_replica/core/system_prompt.py` pro modularizaci systémového promptu.
- V `__init__` implementováno:
    - Načítání `config.yaml` a paměťových souborů (`JULES.md`, `AGENTS.md`).
    - Načítání `GOOGLE_API_KEY` z `.env` a konfigurace klienta Gemini API, včetně offline fallbacku.
- Implementována metoda `_parse_tool_call` pro extrakci kódu ze značek, včetně `dedent` pro víceřádkové bloky.
- Implementována metoda `_build_prompt` pro dynamické sestavení promptu z historie a paměti.
- Implementována základní verze hlavní smyčky v metodě `run`, ověřená v offline režimu.

**Důvod a Kontext:**
- Tento krok představuje implementaci Fáze 2 z technického plánu `PLAN_JULES_REPLICA.md`.
- Cílem bylo vytvořit centrální řídící jednotku ("mozek") agenta, která spravuje jeho životní cyklus a komunikaci s LLM.
- Veškerá logika byla průběžně ověřována pomocí dočasných testovacích skriptů.

**Narazené Problémy a Řešení:**
- Zjištěno, že `python3 -m venv` v tomto prostředí nefunguje standardně (nevytváří `bin` adresář). Problém byl vyřešen instalací závislostí do globálního prostředí `python3 -m pip`.
- `_parse_tool_call` zpočátku selhával na víceřádkových blocích kvůli odsazení. Problém vyřešen použitím `textwrap.dedent`.
- Detekce API klíče byla příliš benevolentní. Byla zpřesněna, aby ignorovala placeholder.

**Dopad na Projekt:**
- Jádro agenta je nyní připraveno.
- Dalším krokem je implementace Fáze 3: Nástroje (`ToolExecutor`), což umožní agentovi vykonávat reálné akce.
---
---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Implementace Systému Nástrojů (Fáze 3)

### Téma: Fáze 3 - Implementace ToolExecutoru a základních nástrojů.

**Popis Práce:**
- Vytvořen soubor `sophia_jules_replica/core/tool_executor.py` s třídou `ToolExecutor`.
- Vytvořeny moduly s nástroji v `sophia_jules_replica/tools/`:
    - `file_system.py` s nástroji `list_files`, `read_file`, `create_file_with_block`.
    - `shell.py` s nástrojem `run_in_bash_session`.
- V `ToolExecutor` implementováno:
    - Dynamické načítání a registrace nástrojů z adresáře `tools/`.
    - Metoda `execute_tool` pro parsování a vykonávání nástrojů v obou syntaxích (standardní a DSL).
- `ToolExecutor` byl propojen s `JulesOrchestrator`em, čímž byl uzavřen celý cyklus od rozhodnutí po akci.

**Důvod a Kontext:**
- Tento krok představuje implementaci Fáze 3 z technického plánu `PLAN_JULES_REPLICA.md`.
- Cílem bylo dát agentovi reálné schopnosti ("ruce"), aby mohl interagovat se svým prostředím.
- Celá funkcionalita byla průběžně ověřována pomocí dočasných testovacích skriptů.

**Narazené Problémy a Řešení:**
- Dynamický import selhával kvůli chybějící cestě k projektu v `sys.path`. Problém byl vyřešen dočasným přidáním cesty během registrace nástrojů.

**Dopad na Projekt:**
- Agent je nyní teoreticky schopen vykonávat jednoduché úkoly.
- Dalším krokem je implementace Fáze 4: Propojení osobnosti (systémového promptu) a finální spojení všech komponent.
---
---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Dokončení Jádra Agenta (Fáze 4)

### Téma: Fáze 4 - Finalizace a vylepšení systémového promptu.

**Popis Práce:**
- Provedena revize kroků Fáze 4, které již byly implementovány v předchozích fázích.
- Do `ToolExecutor` přidána metoda `get_tool_descriptions` pro generování popisů nástrojů.
- Metoda `_build_prompt` v `JulesOrchestrator` byla vylepšena tak, aby dynamicky vkládala seznam dostupných nástrojů a jejich popisů přímo do systémového promptu.

**Důvod a Kontext:**
- Tento krok představuje dokončení Fáze 4 z technického plánu `PLAN_JULES_REPLICA.md`.
- Cílem bylo poskytnout LLM maximální kontext o jeho schopnostech, což je klíčové pro správné rozhodování a výběr nástrojů.
- Tímto je jádro agenta (Orchestrator a Executor) plně propojené a funkční.

**Narazené Problémy a Řešení:**
- Žádné významné problémy se v této fázi nevyskytly.

**Dopad na Projekt:**
- Jádro agenta je nyní kompletní.
- Dalším krokem je implementace Fáze 5: Vytvoření vstupního bodu (`main.py`) pro spouštění agenta s konkrétním úkolem.
---
---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Dokončení Projektu (Fáze 5)

### Téma: Fáze 5 - Vytvoření vstupního bodu a instalačních skriptů.

**Popis Práce:**
- Vytvořen vstupní bod aplikace `sophia_jules_replica/main.py` s použitím `argparse` pro přijetí úkolu.
- V `main.py` implementována detekce a reportování provozních režimů (ONLINE/OFFLINE).
- Vytvořen vývojářský skript `setup.sh` pro automatizaci nastavení prostředí.
- Vytvořen interaktivní uživatelský skript `install.sh` pro snadnou konfiguraci API klíče.
- Všechny komponenty byly otestovány a ověřeny.

**Důvod a Kontext:**
- Tento krok představuje dokončení Fáze 5 z technického plánu `PLAN_JULES_REPLICA.md`.
- Cílem bylo vytvořit spustitelnou aplikaci a usnadnit její instalaci a používání.
- Tímto je celý projekt "Sophia Jules Replica" funkčně dokončen.

**Narazené Problémy a Řešení:**
- Zjištěna nekonzistence v pracovním adresáři shellu, což zpočátku způsobovalo selhání skriptů. Problém byl vyřešen správným používáním relativních cest v rámci `run_in_bash_session`.

**Dopad na Projekt:**
- Projekt "Sophia Jules Replica" je nyní kompletní a spustitelný.
- Uživatelé mohou snadno nastavit prostředí pomocí `install.sh` a spouštět agenta s úkoly pomocí `main.py`.
- Projekt je připraven k odevzdání.
---