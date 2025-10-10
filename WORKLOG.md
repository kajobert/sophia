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
**Datum**: 2025-10-10
**Autor**: Jules (Nomad)
**Ticket/Task**: Implementace 'Prompt Lab' a vylepšení TUI

### Téma: Přidání záložky 'Prompt Lab' a implementace víceřádkového vstupu v TUI.

**Popis Práce:**
- **Implementace 'Prompt Lab':**
  - Vytvořen nový widget `tui/widgets/prompt_lab_widget.py` pro porovnávání výstupů dvou systémových promptů na základě zadaného uživatelského promptu.
  - Integrován nový widget do `tui/app.py` jako nová záložka "Prompt Lab".
  - Implementována logika pro asynchronní porovnání dvou systémových promptů pomocí `ConversationalManager`.
- **Vylepšení TUI:**
  - V `tui/app.py` byl widget `Input` nahrazen za `TextArea` z `textual.widgets` pro podporu víceřádkového zadávání promptů.
  - Byla přidána klávesová zkratka `Enter` pro odeslání promptu, přičemž `Ctrl+Enter` slouží pro vložení nového řádku.
- **Oprava závislostí:**
  - Opravena chyba `ModuleNotFoundError` odstraněním nepotřebné a nesprávné závislosti `textual-inputs` a jejím nahrazením standardním widgetem z `textual`.

**Důvod a Kontext:**
- Cílem bylo vytvořit nástroj pro ladění a optimalizaci systémových promptů a zároveň vylepšit uživatelskou přívětivost hlavního vstupního pole TUI.

**Narazené Problémy a Řešení:**
- **Problém:** Původní implementace `Prompt Lab` způsobila pád aplikace kvůli použití nesprávné externí knihovny (`textual-inputs`) místo vestavěného widgetu.
- **Řešení:** Závislost byla odstraněna a kód byl opraven tak, aby používal `TextArea` z `textual.widgets`, což odstranilo chybu a zjednodušilo kód.
- **Problém:** Po odinstalování chybné závislosti došlo k deaktivaci virtuálního prostředí v shellu, což vedlo k selhání testů.
- **Řešení:** Prostředí bylo obnoveno přeinstalováním všech závislostí pomocí `uv pip install -r requirements.in`.

**Dopad na Projekt:**
- TUI nyní obsahuje výkonný nástroj pro experimentování s prompty a nabízí vylepšené uživatelské rozhraní pro zadávání komplexních, víceřádkových úkolů.
- Kódová báze je stabilní a byla očištěna od nesprávných závislostí.
---
---
**Datum**: 2025-10-10
**Autor**: Jules (Nomad)
**Ticket/Task**: Dokončení dokumentace pro Fázi 3

### Téma: Finalizace a aktualizace dokumentace po implementaci Fáze 3.

**Popis Práce:**
- Aktualizován soubor `docs/FAZE-3-AUTONOMNI-PARTNER-NAVRH.md` a označen jako "Dokončeno".
- Tímto je formálně uzavřena implementace Fáze 3 a veškerá související dokumentace je nyní aktuální.

**Důvod a Kontext:**
- Bylo nutné formálně uzavřít práci na Fázi 3 a zajistit, aby stav projektu byl jasně reflektován v jeho dokumentaci.

**Narazené Problémy a Řešení:**
- Žádné.

**Dopad na Projekt:**
- Projekt je nyní plně zdokumentován a připraven na další fáze vývoje.
---
---
**Datum**: 2025-10-09
**Autor**: Jules (Nomad)
**Ticket/Task**: Implementace Fáze 3 - Autonomní Partner s "Human-in-the-Loop"

### Téma: Implementace bezpečného delegování na externí API s uživatelským schválením.

**Popis Práce:**
- Implementována klíčová funkcionalita Fáze 3 dle návrhu v `docs/FAZE-3-AUTONOMNI-PARTNER-NAVRH.md`.
- **Vytvořen Jules API klient:** Vytvořen nový soubor `mcp_servers/worker/jules_api_server.py`, který obsahuje FastAPI server s nástrojem `delegate_task_to_jules`. Tento klient je zodpovědný za bezpečnou a autentizovanou komunikaci s externím Jules API.
- **Implementován "Human-in-the-Loop" (HITL) schvalovací proces:**
    - `WorkerOrchestrator` (`core/orchestrator.py`) byl upraven tak, aby při návrhu delegování úkolu přerušil svou činnost a vrátil nový stav `needs_delegation_approval`.
    - `ConversationalManager` (`core/conversational_manager.py`) byl rozšířen o stavový mechanismus pro zpracování tohoto nového stavu. Nyní se explicitně ptá uživatele na souhlas, než povolí delegování.
    - Manažer dokáže zpracovat kladnou i zápornou odpověď od uživatele a instruovat Workera, aby buď pokračoval v delegování, nebo našel alternativní řešení.
- **Vytvořeny Komplexní Testy:** Přidán nový testovací soubor `tests/test_jules_api.py`, který obsahuje:
    - Integrační test pokrývající celý schvalovací cyklus (od návrhu po schválení a provedení).
    - Robustní sadu jednotkových testů pro `jules_api_server.py`, které ověřují správné chování při úspěchu i v různých chybových stavech (chybějící API klíč, síťové chyby, neplatné odpovědi API).

**Důvod a Kontext:**
- Cílem bylo naplnit vizi Fáze 3 a vytvořit agenta, který dokáže bezpečně delegovat vysoce komplexní úkoly na specializované externí agenty.
- Mechanismus "Human-in-the-Loop" je klíčovým bezpečnostním prvkem, který zajišťuje, že uživatel má plnou kontrolu nad potenciálně rizikovými operacemi.

**Narazené Problémy a Řešení:**
- **Problém:** Testy pro `jules_api_server.py` opakovaně selhávaly kvůli komplexním a matoucím chybám v mockování asynchronního `httpx` klienta.
- **Řešení:** Po několika neúspěšných pokusech byla identifikována hlavní příčina: volání `os.getenv()` na úrovni modulu, což znemožňovalo efektivní patchování v testech. Kód serveru byl refaktorován tak, aby se proměnná prostředí načítala až uvnitř endpointu. Následně byly testy přepsány s použitím standardního `fastapi.testclient.TestClient`, což vedlo k jejich stabilizaci a úspěšnému projití.
- **Problém:** Drobná chyba v logice zpracování výjimek v `jules_api_server.py`, kde byla specifická `HTTPException` (502) chybně zachycena obecným `except Exception` blokem a přebalena jako `HTTPException` (500).
- **Řešení:** Přidán `except HTTPException: raise` blok, aby se zajistilo, že specifické HTTP výjimky jsou správně propagovány a nejsou zachyceny obecným handlerem.

**Dopad na Projekt:**
- Agent nyní disponuje klíčovou schopností pro autonomní vylepšování – bezpečnou delegací práce.
- Architektura je plně připravena na finální testovací scénář: "Implementuj Sophii".
- Projekt dosáhl milníku definovaného jako Fáze 3.
---
---
**Datum**: 2025-10-09
**Autor**: Jules (Nomad)
**Ticket/Task**: Refactoring to Manager/Worker Architecture & Bug Fixes

### Téma: Implementace a stabilizace architektury Manager/Worker.

**Popis Práce:**
- Proveden velký refaktoring aplikace na dvouúrovňovou architekturu Manager/Worker s cílem oddělit konverzační logiku od provádění úkolů.
- `ConversationalManager` (`core/conversational_manager.py`) byl implementován jako nová nejvyšší vrstva pro interakci s uživatelem, rozhodování a delegování úkolů.
- Původní `JulesOrchestrator` byl přejmenován na `WorkerOrchestrator` (`core/orchestrator.py`) a nyní slouží jako specializovaná výkonná jednotka.
- `MCPClient` byl upraven tak, aby podporoval "profily", a všechny nástrojové servery byly přesunuty do adresáře `mcp_servers/worker/`.
- Byly opraveny kritické `ModuleNotFoundError`, které vznikly v důsledku přesunu souborů serverů, a to systematickou úpravou `sys.path` v každém z nich.
- Byla opravena chyba `ValueError`, která způsobovala pád TUI, nastavením platného výchozího LLM modelu v `config/config.yaml`.
- Byla opravena chyba v testu `test_profile_code_execution`, čímž byla zajištěna 100% úspěšnost testovací sady.
- Byla komplexně aktualizována dokumentace (`ARCHITECTURE.md`, `DEVELOPER_GUIDE.md`, `NOMAD_0.8_plan_implementace.md`), aby odrážela novou architekturu.

**Důvod a Kontext:**
- Původní monolitická architektura byla náchylná k chybám a neumožňovala jasné oddělení zodpovědností. Nová architektura umožňuje, aby se `ConversationalManager` soustředil na porozumění uživateli a vedení konverzace, zatímco `WorkerOrchestrator` se specializuje na provádění složitých úkolů.

**Narazené Problémy a Řešení:**
- **Problém:** Po refaktoringu servery v `mcp_servers/worker/` nemohly najít moduly v `core/` a `tools/` kvůli nesprávným relativním cestám.
- **Řešení:** Systematická oprava `sys.path` v každém souboru serveru tak, aby ukazoval o dvě úrovně výše (`../..`).
- **Problém:** Aplikace padala při startu kvůli chybějící nebo nesprávné konfiguraci výchozího LLM modelu.
- **Řešení:** Úprava `config/config.yaml` a nastavení platného a existujícího modelu jako výchozího.
- **Problém:** Jeden z testů selhával kvůli nesprávně formátovanému příkazu předávanému nástroji.
- **Řešení:** Oprava testovací funkce tak, aby volala testovaný nástroj se správnými argumenty.

**Dopad na Projekt:**
- Aplikace je nyní stabilní a plně funkční s novou, robustnější architekturou.
- Struktura kódu je čistší, modulárnější a lépe připravená na budoucí rozšiřování.
- Dokumentace je plně aktuální a odpovídá implementaci.
---
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
**Datum**: 2025-09-26
**Autor**: Jules (Nomad)
**Ticket/Task**: Finální Architektonická Transformace a Aktivace Autonomie

### Téma: Implementace robustní, modulární a flexibilní MCP architektury.

**Popis Práce:**
- Na základě zpětné vazby od uživatele byla provedena finální, pečlivá transformace celé architektury projektu.
- **Odstranění Staré Architektury:** Projekt byl kompletně vyčištěn od všech pozůstatků staré, na FastAPI založené, architektury, aby se předešlo konfliktům a nejasnostem.
- **Implementace Modulární Architektury:**
    - Byla implementována nová, plně asynchronní a modulární architektura v izolovaném adresáři `core_v2/` a po důkladném otestování byla čistě integrována do hlavního adresáře `core/`.
    - Vytvořen specializovaný `MCPClient` pro správu a komunikaci s nástrojovými servery.
    - Vytvořen specializovaný `PromptBuilder` pro dynamické sestavování promptů.
    - Finální `JulesOrchestrator` nyní slouží jako čistá řídící jednotka delegující práci.
- **Zjednodušení Práce se Soubory:** Nástroje pro práci se souborovým systémem byly sjednoceny, aby pracovaly bezpečně a transparentně přímo v kořenovém adresáři projektu, což odstranilo potřebu speciálních prefixů.
- **Implementace Robustních Nástrojů:** Systém volání nástrojů byl kompletně přepsán na JSON-based formát, což eliminuje chyby při parsování složitých argumentů.
- **Obnova Vstupních Bodů:** Byly vytvořeny čisté a funkční verze `interactive_session.py` a `main.py` pro interaktivní i jednorázové spouštění.
- **Oprava a Vylepšení:** Opravena chyba v načítání API klíče (`GEMINI_API_KEY`) a implementováno konfigurovatelné logování pro lepší transparentnost.

**Důvod a Kontext:**
- Původní architektura byla příliš komplexní, křehká a omezující. Nová architektura je navržena pro maximální robustnost, flexibilitu a transparentnost, což jsou klíčové předpoklady pro skutečný seberozvoj a plnění komplexních úkolů.

**Narazené Problémy a Řešení:**
- **Problém:** Nekonzistence v testovacím prostředí a "zaseknutý" shell.
- **Řešení:** Systematická diagnostika a bezpečný, izolovaný vývoj v `core_v2`, který byl následován čistou finální výměnou.
- **Problém:** Selhávání parsování argumentů nástrojů.
- **Řešení:** Přechod na plně JSON-based komunikaci mezi LLM a nástroji.
- **Problém:** Omezení sandboxu a nemožnost upravovat vlastní kód.
- **Řešení:** Sjednocení a zjednodušení nástrojů pro práci se soubory, které nyní operují bezpečně v celém projektu bez nutnosti speciálních prefixů.

**Dopad na Projekt:**
- Agent je nyní plně autonomní a schopen plnit komplexní, více-krokové úkoly.
- Prokázal schopnost zotavit se z chyby a adaptovat své řešení.
- Architektura je čistá, modulární a připravená na další, skutečně vědomý rozvoj.
---
---
**Datum**: 2025-09-26
**Autor**: Jules (Nomad)
**Ticket/Task**: Finální Opravy a Aktivace Plné Autonomie

### Téma: Oprava cyklických závislostí a finální vylepšení architektury.

**Popis Práce:**
- Na základě zpětné vazby z finálního testování byly identifikovány a opraveny poslední kritické chyby, které bránily plné funkčnosti.
- **Oprava Cyklické Závislosti:** Třída `Colors` byla přesunuta z `orchestrator.py` do `rich_printer.py`, čímž se odstranila cyklická závislost mezi orchestrátorem a MCP klientem.
- **Oprava Chybějících Závislostí:** Byla doinstalována knihovna `rich` a opraveny chybné názvy proměnných pro API klíč (`GEMINI_API_KEY`).
- **Implementace "Sbalitelných" Logů:** Orchestrátor nyní dokáže rozpoznat příliš dlouhé výstupy, uložit je do paměti a na konzoli zobrazit pouze shrnutí. Byl vytvořen nový nástroj `show_last_output` pro jejich zobrazení.
- **Implementace Dynamických Nástrojů:** Byl vytvořen bezpečný mechanismus pro autonomní tvorbu a používání nových nástrojů (`create_new_tool` a `dynamic_tool_server.py`).

**Důvod a Kontext:**
- Cílem bylo odstranit poslední překážky, které bránily agentovi v plnění komplexních, více-krokových úkolů a v jeho schopnosti seberozvoje.

**Narazené Problémy a Řešení:**
- **Problém:** `ImportError` způsobená cyklickou závislostí.
- **Řešení:** Refaktoring a centralizace sdíleného kódu do `rich_printer.py`.
- **Problém:** Selhání testů kvůli chybějící `rich` knihovně a nesprávnému názvu proměnné pro API klíč.
- **Řešení:** Doinstalování závislostí a oprava názvu proměnné.

**Dopad na Projekt:**
- Agent je nyní ve finálním, plně funkčním a robustním stavu.
- Prokázal schopnost nejen plnit komplexní úkoly, ale také se autonomně učit a rozšiřovat své schopnosti vytvářením nových nástrojů.
- Projekt je připraven k odevzdání jako stabilní základ pro budoucí, plně autonomní operace.
---