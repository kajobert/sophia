# Sophia AMI 1.0: Detailní Plán Implementace

## Úvod

Tento dokument poskytuje detailní, technický a fázovaný implementační plán pro transformaci Sophie z reaktivního nástroje na proaktivního, autonomního agenta, založený na vizi popsané v `docs/01_SOPHIA AMI 1.0.md`.

Plán je rozdělen do pěti strategických fází. Každá fáze je rozdělena na zvládnutelné, samostatné úkoly navržené tak, aby byly dosažitelné během jedné vývojové session. Každý úkol obsahuje jasný cíl, seznam ovlivněných souborů, podrobný akční plán a technické poznámky založené na aktuálních nejlepších postupech a výzkumu.

## Fáze 1: Aktivace "Kognitivní Smyčky" (Proaktivní 24/7 Provoz)

**Cíl:** Přepnout Sophii z reaktivního, příkazově řízeného režimu na plně autonomního, 24/7 běžícího daemona, postaveného na její stávající event-driven architektuře. Tato fáze zavádí základní "srdeční tep" (heartbeat) a mechanismus pro neustálé učení se z externích poznámek.

---

### Úkol 1.1: Refaktor `run.py` pro Nepřetržitý Provoz

*   **Cíl:** Zjednodušit vstupní bod aplikace tak, aby výhradně spouštěl Kernel v trvalém, event-driven režimu.
*   **Ovlivněné Soubory:**
    *   `run.py`
*   **Akční Plán:**
    1.  Odstranit veškerou logiku pro zpracování argumentů příkazového řádku (`argparse`) související s reaktivním spuštěním (`--once`, `--no-webui` atd.).
    2.  Funkce `async def main()` v `run.py` bude zjednodušena tak, aby prováděla pouze dvě akce:
        *   Inicializovala `Kernel`.
        *   Spustila hlavní, nikdy nekončící smyčku událostí voláním nové metody, např. `await kernel.run_autonomous_mode()`.
*   **Technické Poznámky:**
    *   Tato změna ustanoví smyčku událostí v `core/event_loop.py` jako jediný a výchozí způsob provozu, což zjednodušuje architekturu.

---

### Úkol 1.2: Oddělení Uživatelského Vstupu pomocí Sběrnice Událostí (Event Bus)

*   **Cíl:** Přesměrovat všechny externí vstupy, jako jsou ty z WebUI, přes centrální sběrnici událostí, aby se standardizovalo jejich zpracování.
*   **Ovlivněné Soubory:**
    *   `plugins/interface_webui.py`
    *   `core/event_bus.py` (pokud ještě není plně implementován)
    *   `core/kernel.py`
*   **Akční Plán:**
    1.  Upravit FastAPI endpointy v `interface_webui.py` (např. `/chat`). Tyto endpointy **již nesmí** volat metody Kernelu přímo.
    2.  Místo toho budou publikovat událost, například: `event_bus.publish(Event(EventType.USER_INPUT_RECEIVED, data={'source': 'webui', 'text': ...}))`.
    3.  `Kernel` se přihlásí k odběru události `USER_INPUT_RECEIVED` a spustí příslušný pracovní postup zpracování.
*   **Technické Poznámky:**
    *   Tímto se oddělí vstupní rozhraní od jádra logiky, což v budoucnu umožní více nezávislých zdrojů vstupu (např. Slack, e-mail).
    *   `asyncio.Queue` je vhodnou a jednoduchou implementací pro sběrnici událostí, pokud již neexistuje složitější řešení.

---

### Úkol 1.3: Implementace Proaktivního "Srdečního Tepu" a Zpracování Nápadů

*   **Cíl:** Vytvořit opakující se spouštěč pro proaktivní úkoly a integrovat sledování souboru pro zpracování nových nápadů z `roberts-notes.txt`.
*   **Ovlivněné Soubory:**
    *   `core/event_loop.py`
    *   **Nový Plugin:** `plugins/core_proactive_agent.py`
*   **Akční Plán:**
    1.  V hlavní smyčce `core/event_loop.py` přidat periodický časovač (např. `asyncio.sleep(60)`).
    2.  Při každém tiknutí časovače publikovat událost `PROACTIVE_HEARTBEAT`.
    3.  Vytvořit nový plugin, `core_proactive_agent.py`. Tento plugin bude zodpovědný za orchestraci autonomních aktivit.
    4.  Plugin se přihlásí k odběru `PROACTIVE_HEARTBEAT`.
    5.  Po obdržení "srdečního tepu" plugin provede následující:
        *   Zkontroluje změny v souboru `docs/roberts-notes.txt`.
        *   Pokud se soubor změnil, přečte nový obsah, publikuje událost `NEW_IDEA_DETECTED` s obsahem a spustí plánovací sekvenci pro analýzu a naplánování nápadu.
*   **Technické Poznámky:**
    *   Pro sledování souborů poskytuje knihovna `watchdog` robustní, multiplatformní, event-based API, které lze integrovat s `asyncio` pomocí `loop.run_in_executor`. To je efektivnější než dotazování `os.path.getmtime`.
    *   Proaktivní agent funguje jako centrální uzel pro autonomní chování, čímž udržuje hlavní smyčku událostí čistou a jednoduchou.

---

### Úkol 1.4: Aktivace Plánovače Spánku

*   **Cíl:** Umožnit Sophii přejít do stavu nízké aktivity ("spánku") pro provádění úkolů konsolidace paměti a sebereflexe.
*   **Ovlivněné Soubory:**
    *   `plugins/core_sleep_scheduler.py`
*   **Akční Plán:**
    1.  Stávající plugin `core_sleep_scheduler.py` se přihlásí k odběru události `PROACTIVE_HEARTBEAT`.
    2.  Po obdržení události zkontroluje podmínky pro spánek (např. denní doba, žádná uživatelská aktivita po dobu X minut) na základě konfiguračního souboru (např. `config/autonomy.yaml`).
    3.  Pokud jsou podmínky splněny, publikuje událost `DREAM_TRIGGER`, čímž signalizuje začátek spánkového cyklu.
*   **Technické Poznámky:**
    *   Tímto se znovu aktivuje stávající funkcionalita (dle Mise #13) a integruje se do nové autonomní smyčky.

## Fáze 2: Implementace Inteligentního Hybridního Routeru

**Cíl:** Vybudovat jádro provozní efektivity Sophie tím, že se umožní autonomní správa a výběr mezi lokálními a cloudovými poskytovateli LLM.

---

### Úkol 2.1: Vylepšení Routeru pro Rozpoznávání Poskytovatelů

*   **Cíl:** Vylepšit `CognitiveTaskRouter` tak, aby vybíral nejen model, ale i správného *poskytovatele* (a tím i správný tool plugin) pro daný úkol.
*   **Ovlivněné Soubory:**
    *   `plugins/cognitive_task_router.py`
    *   `config/model_strategy.yaml`
*   **Akční Plán:**
    1.  Rozšířit schéma `config/model_strategy.yaml`. Každá položka modelu musí nyní obsahovat klíč `provider` (např. `provider: 'openrouter'` nebo `provider: 'ollama'`).
    2.  Upravit logiku routeru. Po výběru modelu pro úkol musí přečíst klíč `provider`.
    3.  Na základě poskytovatele router naformátuje `tool_call` tak, aby cílil na příslušný plugin:
        *   `openrouter` -> `tool_llm.execute(...)`
        *   `ollama` -> `tool_local_llm.execute(...)` (za předpokladu, že tento plugin existuje).
*   **Technické Poznámky:**
    *   Tím se router stává centrálním rozhodovacím bodem pro provádění LLM, což abstrahuje volbu poskytovatele od ostatních pluginů.

---

### Úkol 2.2: Vytvoření Pluginu `ModelManager`

*   **Cíl:** Umožnit Sophii spravovat své vlastní lokální LLM prostředí pomocí dedikovaného tool pluginu.
*   **Ovlivněné Soubory:**
    *   **Nový Plugin:** `plugins/tool_model_manager.py`
    *   `plugins/tool_bash.py` (jako závislost)
*   **Akční Plán:**
    1.  Vytvořit nový plugin `tool_model_manager.py`.
    2.  Implementovat následující metody, které budou interně používat `tool_bash.execute` pro interakci s `ollama` CLI:
        *   `list_local_models()`: Spustí `ollama list`, zpracuje výstup a vrátí strukturovaný seznam (např. JSON).
        *   `pull_local_model(model_name: str)`: Spustí `ollama pull [model_name]` a streamuje výstup.
        *   `get_model_info(model_name: str)`: Spustí `ollama show --json [model_name]` a vrátí zpracované JSON informace.
*   **Technické Poznámky:**
    *   Tento plugin poskytuje klíčovou vrstvu abstrakce. Ostatní pluginy mohou nyní spravovat modely, aniž by musely znát konkrétní příkazy shellu, což činí systém modulárnějším a robustnějším.

---

### Úkol 2.3: Implementace Samostatné Konfigurace Modelů

*   **Cíl:** Umožnit Sophii autonomně aktualizovat svou vlastní konfigurační strategii modelů.
*   **Ovlivněné Soubory:**
    *   `plugins/tool_model_manager.py`
    *   `plugins/tool_file_system.py` (jako závislost)
*   **Akční Plán:**
    1.  Přidat novou metodu do `tool_model_manager.py`: `add_model_to_strategy(task_type: str, model_name: str, provider: str, size: str)`.
    2.  Tato metoda použije `tool_file_system.read_file` k načtení `config/model_strategy.yaml`.
    3.  Poté programově přidá novou konfiguraci modelu pod zadaný `task_type`.
    4.  Nakonec použije `tool_file_system.write_file` k uložení aktualizované konfigurace.
*   **Technické Poznámky:**
    *   Použití knihovny jako `PyYAML` je nezbytné pro bezpečnou a spolehlivou úpravu souborů YAML, která pokud možno zachová komentáře a strukturu. Tato metoda dává Sophii silnou schopnost sebekonfigurace.

## Fáze 3: "Rámec pro Sebe-Ladění" (Autonomní Růst)

**Cíl:** Vytvořit kompletní zpětnovazební smyčku, kde Sophia může snít, reflektovat svá selhání, formulovat hypotézy pro zlepšení a automaticky implementovat a testovat tato zlepšení.

---

### Úkol 3.1: Aktivace Konsolidátoru Paměti ("Snění")

*   **Cíl:** Spustit stávající logiku konsolidace paměti jako první krok v cyklu "spánku".
*   **Ovlivněné Soubory:**
    *   `plugins/cognitive_memory_consolidator.py`
*   **Akční Plán:**
    1.  Plugin `cognitive_memory_consolidator.py` se přihlásí k odběru události `DREAM_TRIGGER` (publikované Plánovačem spánku v Úkolu 1.4).
    2.  Po obdržení události spustí svou stávající logiku pro konsolidaci paměti (např. sumarizace nedávných událostí, přesun dat z operační paměti do dlouhodobé sémantické paměti).
    3.  Po dokončení publikuje událost `DREAM_COMPLETE`, aby signalizoval začátek další fáze: reflexe.
*   **Technické Poznámky:**
    *   Tímto se formálně integruje koncept "snění" do autonomní smyčky, což z něj činí předpoklad pro sebereflexi.

---

### Úkol 3.2: Vytvoření Pluginu `CognitiveReflection`

*   **Cíl:** Vyvinout plugin, který analyzuje minulá selhání a generuje konkrétní, testovatelné hypotézy, jak se zlepšit.
*   **Ovlivněné Soubory:**
    *   **Nový Plugin:** `plugins/cognitive_reflection.py`
    *   `plugins/memory_sqlite.py`
*   **Akční Plán:**
    1.  Vytvořit nový plugin `cognitive_reflection.py`. Přihlásí se k odběru události `DREAM_COMPLETE`.
    2.  Po aktivaci použije `memory_sqlite.py` k dotazování do databáze operačního sledování na všechny operace, kde `success = False`.
    3.  Pro každé selhání použije výkonný "Plánovač" LLM k analýze kontextu, logů a uživatelského požadavku.
    4.  Cílem analýzy je vygenerovat **hypotézu** o hlavní příčině (např. "Hypotéza H1: Docstring pro `fs.write` je pro menší modely nejednoznačný. Přidání příkladu ve formátu JSON by zlepšilo srozumitelnost.").
    5.  Vygenerovaná hypotéza bude uložena do nové tabulky `hypotheses` v databázi SQLite a bude publikována událost `HYPOTHESIS_CREATED`.
*   **Technické Poznámky:**
    *   Toto je analytické jádro smyčky pro sebe-ladění. Kvalita hypotéz je kritická, proto se pro tento krok doporučuje použít nejschopnější dostupný LLM.

---

### Úkol 3.3: Vytvoření Pluginu `CognitiveSelfTuning`

*   **Cíl:** Reagovat na hypotézu úpravou kódu v bezpečném, izolovaném prostředí (sandbox), otestovat změnu a vytvořit pull request, pokud je změna přínosná.
*   **Ovlivněné Soubory:**
    *   **Nový Plugin:** `plugins/cognitive_self_tuning.py`
    *   `plugins/tool_code_reader.py` (závislost)
    *   `plugins/tool_git.py` (závislost, může vyžadovat vytvoření/vylepšení)
    *   `plugins/tool_model_evaluator.py` (závislost)
*   **Akční Plán:**
    1.  Vytvořit nový plugin `cognitive_self_tuning.py`, který se přihlásí k odběru `HYPOTHESIS_CREATED`.
    2.  **Úprava Kódu:**
        *   Přečte hypotézu (např. H1).
        *   Použije `tool_code_reader.py` k načtení relevantního souboru (např. `plugins/tool_file_system.py`).
        *   Použije "Expertní" cloudový model k vygenerování úpravy kódu na základě hypotézy.
        *   Zapíše upravený kód do izolovaného umístění, např. `sandbox/tuning/v1/tool_file_system.py`.
    3.  **Evaluace v Sandboxu:**
        *   Použije `tool_model_evaluator.py` ke spuštění benchmarku. Tento evaluátor musí být vylepšen tak, aby dynamicky načítal a testoval verzi pluginu ze sandboxu proti "Pracovnímu" (např. 8B lokálnímu) modelu.
    4.  **Nasazení přes Git:**
        *   Pokud benchmark ukáže jasné zlepšení, plugin použije `tool_git.py` k:
            *   Vytvoření nové větve (např. `feature/sophia-tuning-h1`).
            *   Commitnutí změny ze sandboxu.
            *   Pushnutí větve do vzdáleného repozitáře.
            *   Vytvoření pull requestu do dedikované větve (např. `master-sophia`), jak je definováno v `config/autonomy.yaml`.
*   **Technické Poznámky:**
    *   `GitTool` bude pravděpodobně potřeba vytvořit nebo významně vylepšit, s použitím knihovny jako `GitPython` pro poskytnutí robustního API pro git operace.
    *   Dynamické načítání modulu ze sandboxu pro testování je kritický krok. `importlib` lze použít k dosažení tohoto cíle manipulací s `sys.path`.

## Fáze 4: Pokročilý Vhled (Graph RAG & ACI)

**Cíl:** Poskytnout Sophii hlubší, strukturální porozumění její vlastní kódové základně a implementovat holistický benchmark kvality (ACI).

---

### Úkol 4.1: Vytvoření Pluginu `Neo4jTool`

*   **Cíl:** Vytvořit dedikovaný nástroj pro interakci s grafovou databází Neo4j.
*   **Ovlivněné Soubory:**
    *   **Nový Plugin:** `plugins/tool_neo4j.py`
*   **Akční Plán:**
    1.  Vytvořit plugin `tool_neo4j.py`.
    2.  Bude používat oficiální Python ovladač `neo4j`.
    3.  Implementovat základní metody:
        *   `execute_query(query: str, parameters: dict)`: Spustí Cypher dotaz proti databázi.
        *   `add_node(label: str, properties: dict)`
        *   `add_relationship(source_node_id: int, target_node_id: int, rel_type: str, properties: dict)`
*   **Technické Poznámky:**
    *   Připojovací údaje (URI, uživatel, heslo) by měly být spravovány přes `config/settings.yaml`. Plugin by měl řešit connection pooling a správu session.

---

### Úkol 4.2: Vytvoření Pluginu `CognitiveGraphRAG` (Indexer)

*   **Cíl:** Zpracovat celou Python kódovou základnu a reprezentovat ji jako znalostní graf v Neo4j.
*   **Ovlivněné Soubory:**
    *   **Nový Plugin:** `plugins/cognitive_graph_rag.py`
    *   `plugins/tool_code_reader.py` (závislost)
    *   `plugins/tool_neo4j.py` (závislost)
*   **Akční Plán:**
    1.  Vytvořit plugin `cognitive_graph_rag.py`. Přihlásí se k odběru události `DREAM_TRIGGER` pro provádění periodické re-indexace.
    2.  Použít `tool_code_reader.py` k vypsání a přečtení všech `*.py` souborů v projektu.
    3.  Pro každý soubor použít vestavěný Python modul `ast` (Abstract Syntax Tree) k parsování kódu do stromové struktury.
    4.  Procházet AST k identifikaci uzlů jako jsou třídy, funkce, volání metod a importy.
    5.  Použít `tool_neo4j.py` k naplnění grafu uzly a vztahy, jako jsou:
        *   `(Class)-[:HAS_METHOD]->(Method)`
        *   `(Method)-[:CALLS_METHOD]->(Method)`
        *   `(Module)-[:IMPORTS]->(Module)`
*   **Technické Poznámky:**
    *   Modul `ast` je mocný a bezpečný způsob, jak analyzovat Python kód bez jeho spuštění. Tento úkol je složitý a vyžaduje dobré porozumění struktuře AST.

---

### Úkol 4.3: Implementace `analyze_code_structure` (Dotazovací Nástroj)

*   **Cíl:** Zpřístupnit znalostní graf jako nový silný nástroj pro Sophii.
*   **Ovlivněné Soubory:**
    *   `plugins/cognitive_graph_rag.py`
*   **Akční Plán:**
    1.  Přidat novou tool metodu do `cognitive_graph_rag.py`: `analyze_code_structure(query: str) -> str`.
    2.  Tato metoda přijme dotaz v přirozeném jazyce (např. "Které pluginy volají metodu `tool_bash.execute`?").
    3.  Použije LLM k překladu dotazu v přirozeném jazyce na formální Cypher dotaz pro Neo4j.
    4.  Spustí Cypher dotaz pomocí `tool_neo4j.py`.
    5.  Zformátuje výsledky do lidsky čitelného souhrnu a vrátí ho.
*   **Technické Poznámky:**
    *   Tato technika je známá jako Text-to-Cypher a je silnou aplikací LLM pro interakci se strukturovanými daty.

---

### Úkol 4.4: Implementace Holistického Benchmarku (ACI)

*   **Cíl:** Integrovat finální kontrolu kvality do procesu sebe-ladění, která hodnotí změny oproti základním principům DNA Sophie.
*   **Ovlivněné Soubory:**
    *   `plugins/cognitive_self_tuning.py`
    *   `plugins/tool_model_evaluator.py`
    *   `config/prompts/sophia_dna.txt`
*   **Akční Plán:**
    1.  Přidat novou metodu do `tool_model_evaluator.py`: `evaluate_holistic_quality(code_change_summary: str) -> dict`.
    2.  Tato metoda vezme souhrn navrhované změny a obsah `sophia_dna.txt`.
    3.  Pošle tyto informace "Expertnímu" cloudovému modelu s promptem, který ho požádá o ohodnocení změny na základě základních principů (např. Empatie, Růst, Etika, Sebeuvědomění).
    4.  Plugin `cognitive_self_tuning.py` zavolá tuto metodu *poté*, co projde technický benchmark.
    5.  Pull Request bude vytvořen pouze tehdy, pokud jsou přijatelné jak technický benchmark, tak ACI skóre. ACI skóre bude zahrnuto v popisu PR.
*   **Technické Poznámky:**
    *   ACI (Autonomous Cognitive Index) skóre je kvalitativní míra. Design promptu je klíčový pro získání smysluplných a konzistentních výsledků.

## Fáze 5: "Phoenix Protocol" (Autonomní Obnova)

**Cíl:** Vybudovat robustní, externí dohledový systém (watchdog), který dokáže obnovit Sophii po kritickém selhání a umožní jí poučit se z vlastních fatálních chyb.

---

### Úkol 5.1: Vytvoření Externího Skriptu `guardian.py`

*   **Cíl:** Vyvinout jednoduchý, samostatný Python skript, který bude fungovat jako procesový supervisor pro hlavní aplikaci Sophie.
*   **Ovlivněné Soubory:**
    *   **Nový Skript:** `guardian.py` (v kořenovém adresáři projektu)
*   **Akční Plán:**
    1.  Vytvořit `guardian.py`. Tento skript **nebude** plugin a bude mít minimální závislosti.
    2.  Jeho hlavní funkcí je spustit hlavní aplikaci (`python run.py`) jako podproces pomocí `subprocess.Popen`.
    3.  Musí zachytávat `stdout` a `stderr` podřízeného procesu v reálném čase a streamovat je jak do své vlastní konzole, tak do kombinovaného log souboru (např. `logs/guardian.log`).
*   **Technické Poznámky:**
    *   Použití `subprocess.Popen` s `stdout=subprocess.PIPE` a `stderr=subprocess.PIPE` umožňuje neblokující monitorování logů v reálném čase. Knihovna jako `psutil` může být použita pro hlubší sledování zdraví podřízeného procesu.

---

### Úkol 5.2: Implementace Detekce Pádu a Logování pro Obnovu

*   **Cíl:** Umožnit strážci detekovat, kdy hlavní aplikace spadla, a zalogovat specifickou chybu, která to způsobila.
*   **Akční Plán:**
    1.  Hlavní smyčka v `guardian.py` bude periodicky kontrolovat `process.poll()`. Hodnota jiná než None značí, že proces skončil.
    2.  Pokud je návratový kód nenulový (což značí pád):
        *   Strážce přečte veškerý zbývající výstup z `stderr`.
        *   Uloží tento finální chybový výstup do log souboru s časovým razítkem (např. `logs/crash_20251105_093000.log`).
        *   Poté restartuje aplikaci a předá cestu k tomuto logu jako argument příkazového řádku: `python run.py --recover-from-crash logs/crash_...log`.
*   **Technické Poznámky:**
    *   Tímto se vytvoří uzavřená smyčka, kde jsou informace o pádu zachovány a okamžitě vráceny do systému při restartu.

---

### Úkol 5.3: Implementace Logiky Obnovy v Kernelu

*   **Cíl:** Umožnit Kernelu rozpoznat, že je spouštěn v režimu obnovy, a použít log o pádu k iniciaci sebereflexe.
*   **Ovlivněné Soubory:**
    *   `core/kernel.py`
    *   `plugins/cognitive_reflection.py`
*   **Akční Plán:**
    1.  V `kernel.initialize()` (nebo podobné startovací metodě) přidat logiku pro kontrolu `sys.argv` na přítomnost příznaku `--recover-from-crash`.
    2.  Pokud je příznak přítomen, Kernel přečte zadaný log soubor.
    3.  Poté publikuje speciální událost `SYSTEM_RECOVERY`, s obsahem logu o pádu jako payloadem.
    4.  Plugin `cognitive_reflection.py` (z Fáze 3) se přihlásí k odběru této události. Po jejím obdržení okamžitě vytvoří hypotézu s vysokou prioritou k řešení fatální chyby.
*   **Technické Poznámky:**
    *   Tímto Sophia získá "paměť" na svou vlastní zkázu, což přemění kritické selhání na vysoce prioritní příležitost k učení.

---

### Úkol 5.4: Implementace Rollbacku při Destruktivním Selhání

*   **Cíl:** Vytvořit finální záchrannou síť, kde strážce může automaticky vrátit zpět špatnou změnu kódu, pokud způsobuje opakované, rychlé pády.
*   **Akční Plán:**
    1.  Skript `guardian.py` bude udržovat počítadlo pádů (např. počet pádů během 5minutového okna).
    2.  Pokud toto počítadlo překročí prahovou hodnotu (např. 5 pádů), značí to destruktivní zpětnovazební smyčku.
    3.  Strážce poté provede příkaz pro rollback pomocí `subprocess.run`:
        *   `git reset --hard HEAD~1` (na větvi specifikované v `config/autonomy.yaml`, např. `master-sophia`).
    4.  Po rollbacku restartuje Sophii naposledy, opět s příznakem `--recover-from-crash`, a předá jí log z *prvního* pádu v sérii.
*   **Technické Poznámky:**
    *   Toto je ultimátní mechanismus obnovy. Starší, stabilní verze Sophie je znovu spuštěna a je okamžitě informována o chybě, kterou udělala její "budoucí já", což jí umožňuje analyzovat a potenciálně opravit problém bez opakování chyby.
