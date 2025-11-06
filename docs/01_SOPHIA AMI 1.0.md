# Definitivní Plán Implementace: Sophia AMI (Autonomous Mind Interface)

**Analýza Stav:** Projekt Sophia má excelentní základ v podobě architektury "Kernel + Pluginy" a již implementovaných, ale "spících" pokročilých komponent pro autonomii (Event Loop, Task Queue, Process Manager, Sleep Scheduler).

**Cíl:** Aktivovat, propojit a rozšířit tyto komponenty a přeměnit Sophii z reaktivního nástroje na proaktivního, 24/7 běžícího autonomního agenta, který se sám učí, optimalizuje a je robustní vůči selhání.

---

### Fáze 1: Aktivace "Kognitivní Smyčky" (Proaktivní 24/7 Provoz)

**Cíl:** Přepnout Sophii z reaktivního režimu (čekání na `--once` nebo `input()`) na plně autonomní, 24/7 běžící daemon postavený na již existující event-driven architektuře (Mise #17).

1.  **Aktivace Event Loop (Soubor: `run.py`)**
    * **Akce:** Upravit `run.py`. Odstranit veškerou logiku spojenou s `argparse` pro reaktivní běh (`--once`, `--no-webui` atd.).
    * **Akce:** Hlavní funkce `async def main()` v `run.py` bude mít jediný úkol: inicializovat `Kernel` a spustit hlavní, nikdy nekončící smyčku: `await kernel.run_event_driven()`.
    * **Důsledek:** Tím se `core/event_loop.py` stane výchozím a jediným způsobem běhu.

2.  **Oddělení Režimu "Bdění" (Soubory: `interface_webui.py`, `core/event_loop.py`)**
    * **API Vstup:** Upravit `interface_webui.py`. FastAPI endpointy (např. `/chat`) již *nesmí* přímo volat `kernel.process_input()`. Místo toho musí publikovat událost do `core/event_bus.py`: `event_bus.publish(Event(EventType.USER_INPUT, data={...}))`.
    * **Proaktivní Práce:** Do hlavní smyčky v `core/event_loop.py` přidat periodický (např. 1x za 60s) trigger, který publikuje událost `Event(EventType.PROACTIVE_HEARTBEAT)`.

3.  **Aktivace Režimu "Spánku" (Soubor: `core_sleep_scheduler.py`)**
    * **Akce:** Tento existující plugin (Mise #13) se přihlásí k odběru `EventType.PROACTIVE_HEARTBEAT`.
    * **Akce:** Při obdržení události zkontroluje podmínky pro spánek (např. nízká aktivita, časový plán dle `config/autonomy.yaml`).
    * **Akce:** Pokud jsou podmínky splněny, publikuje novou, oddělenou událost: `Event(EventType.DREAM_TRIGGER)`.

---

### Fáze 2: Implementace Inteligentního Hybridního Routeru

**Cíl:** Vytvořit srdce provozní efektivity. Rozšířit existující `cognitive_task_router.py` (Mise #8) tak, aby mohl autonomně spravovat a volit mezi lokálními a cloudovými modely.

1.  **Rozšíření Routeru (Soubor: `cognitive_task_router.py`)**
    * **Akce:** Upravit router, aby četl rozšířený `config/model_strategy.yaml`. Ten musí nově obsahovat klíč `provider` (např. `provider: 'ollama'` vs. `provider: 'openrouter'`).
    * **Akce:** Router musí dynamicky delegovat úkoly správnému pluginu:
        * `provider: 'openrouter'` → volá `tool_llm.py` (existující).
        * `provider: 'ollama'` → volá `tool_local_llm.py` (existující).
    * **Akce:** Musí podporovat různé velikosti modelů (8B "Tahoun", 30B+ "Plánovač").

2.  **Nový Plugin: `plugins/tool_model_manager.py` (Autonomní Instalace)**
    * **Cíl:** Dává Sophii kontrolu nad vlastním lokálním prostředím LLM.
    * **Metody:**
        * `list_local_models()`: Použije `tool_bash.py` k volání `ollama list` a naparsuje výstup.
        * `pull_local_model(model_name: str)`: Použije `tool_bash.py` k volání `ollama pull [model_name]`.
        * `configure_gpu_offload(model_name: str, layers: int)`: Upraví konfiguraci (např. v `config/settings.yaml`) pro `tool_local_llm.py`, aby nastavila `n_gpu_layers` (pro GGUF GPU Offloading).
        * `add_model_to_strategy(task_type: str, model_name: str, provider: str)`: Použije `tool_file_system.py` k načtení, úpravě a uložení `config/model_strategy.yaml`. Tím se Sophia stává sama konfigurovatelnou.

---

### Fáze 3: "Self-Tuning Framework" (Autonomní Růst a Učení)

**Cíl:** Propojit cykly "Spánku" a "Růstu" a vytvořit tak mechanismus, kterým se Sophia sama optimalizuje pro jakýkoli model, který má k dispozici.

1.  **Aktivace "Snění" (Soubor: `cognitive_memory_consolidator.py`)**
    * **Trigger:** Tento existující plugin (Mise #13) se přihlásí k odběru události `EventType.DREAM_TRIGGER`.
    * **Akce:** Spustí svou stávající logiku konsolidace paměti (přesun `operation_tracking` do `memory_chroma.py`). Po dokončení publikuje `Event(EventType.DREAM_COMPLETE)`.

2.  **Nový Plugin: `plugins/cognitive_reflection.py` ("Reflexe")**
    * **Trigger:** Přihlásí se k odběru `EventType.DREAM_COMPLETE`.
    * **Proces:**
        1.  Použije `memory_sqlite.py` k načtení záznamů z `operation_tracking`, kde `success = False` (z `OFFLINE_DREAMING.md`).
        2.  Pro každý neúspěch použije "Plánovač" (30B+ LLM) k analýze logu a kontextu.
        3.  Vygeneruje **hypotézu** (např. "Hypotéza H1: Docstring pro `fs.write` je nejasný pro 8B model. Navrhuji přidat JSON příklad.").
        4.  Uloží hypotézu do nové tabulky `hypotheses` (nutno přidat do `memory_sqlite.py`). Publikuje `Event(EventType.HYPOTHESIS_CREATED)`.

3.  **Nový Plugin: `plugins/cognitive_self_tuning.py` ("Růst")**
    * **Trigger:** Přihlásí se k odběru `EventType.HYPOTHESIS_CREATED`.
    * **Proces (Testování hypotézy):**
        1.  Načte hypotézu (např. H1).
        2.  Použije `tool_code_reader.py` (Mise #11) k načtení `plugins/tool_file_system.py`.
        3.  Použije "Expert" (Cloud) model k aplikaci změny (vygeneruje nový docstring).
        4.  Zapíše upravený soubor do *dočasného sandboxu* (např. `sandbox/temp_plugin/tool_file_system_v2.py`).
        5.  Použije `tool_model_evaluator.py` (Mise #7) ke spuštění benchmarku, který dynamicky načte tento *sandboxový* plugin a otestuje jej proti "Tahoun" (8B) modelu.
    * **Nasazení:**
        1.  Pokud benchmark prokáže zlepšení (např. úspěšnost 99 % vs. 92 %), použije `tool_github.py` (Mise #9) k vytvoření Pull Requestu do větve `master-sophia` (definované v `config/autonomy.yaml`).

---

### Fáze 4: Pokročilý Vhled (Graph RAG & ACI)

**Cíl:** Implementovat dlouhodobou vizi: holistické měření (ACI) a strukturální sebe-analýzu (Graph RAG).

1.  **Nový Plugin: `plugins/cognitive_graph_rag.py` ("Rentgenový Zrak")**
    * **Indexer (Trigger: `EventType.DREAM_TRIGGER`)**:
        1.  Použije `tool_code_reader.py` k načtení všech `*.py` souborů.
        2.  Pomocí vestavěného Python modulu `ast` (z našeho průzkumu) naparsuje kód.
        3.  Vytvoří **Nový Plugin: `plugins/tool_neo4j.py`** (pro připojení k Neo4j).
        4.  Naplní graf uzly a vztahy: `(Třída)-[:OBSAHUJE]->(Metoda)`, `(Metoda)-[:VOLÁ]->(Plugin)`.
    * **Query Tool (Nová schopnost pro Sophii)**:
        1.  Vytvoří metodu `analyze_code_structure(dotaz: str)`.
        2.  Tato metoda zkombinuje sémantické vyhledávání (přes `memory_chroma.py`) a strukturální dotazování (přes `tool_neo4j.py`) k zodpovězení dotazů jako: "Které pluginy volají metodu `tool_bash.execute`?".

2.  **Implementace "Holistického Benchmarku (ACI)" (Úprava `cognitive_self_tuning.py`)**
    * **Akce:** Do procesu Fáze 3 (Self-Tuning) přidat nový krok.
    * *Po* úspěšném technickém benchmarku zavolá novou metodu `tool_model_evaluator.py::evaluate_holistic_quality()`.
    * **Akce:** Tato metoda vezme výstupy z benchmarku a DNA principy (z `config/prompts/sophia_dna.txt`) a pošle je "Expert" (Cloud) modelu s dotazem na ohodnocení (Empatie, Růst, Etika, Sebe-uvědomění).
    * **Výsledek:** Výsledné **ACI skóre ("Sophia Průvan")** se uloží. PR je vytvořen pouze tehdy, pokud je technické *i* ACI skóre přijatelné.

---

### Fáze 5: "Phoenix Protocol" (Autonomní Obnova po Pádu)

**Cíl:** Implementovat robustnost. Vytvořit externí dohled, který Sophii obnoví po kritickém pádu a poskytne jí "pohled do budoucnosti" (do vlastního selhání).

**Architektura:** Toto nemůže být plugin. Musí to být externí "hlídací" proces.

1.  **Nový Skript: `guardian.py` (Externí Watchdog)**
    * **Popis:** Jednoduchý, robustní Python skript, který *není* plugin.
    * **Úkol:** Spustit hlavní `python run.py` (který startuje Fázi 1) jako `subprocess.Popen`.
    * **Úkol:** Neustále monitoruje `stdout` a `stderr` podprocesu a streamuje je do hlavního logu (např. `logs/sentinel_combined.log`).

2.  **Detekce Pádu a Obnova**
    * **Akce:** Hlídací smyčka v `guardian.py` kontroluje stav podprocesu.
    * **Akce:** Pokud detekuje pád (non-zero exit code):
        1.  Zazálohuje poslední chybový výstup do `logs/last_crash_YYYYMMDD_HHMMSS.log`.
        2.  Spustí `python run.py` znovu, ale tentokrát s argumentem: `python run.py --recovery-from-crash logs/last_crash_YYYYMMDD_HHMMSS.log`.

3.  **Logika Obnovy (Úprava `core/kernel.py`)**
    * **Akce:** V `kernel.initialize()` zkontrolovat `sys.argv` pro `--recovery-from-crash`.
    * **Akce:** Pokud je přítomen, načíst tento log a publikovat speciální událost: `Event(EventType.SYSTEM_RECOVERY, data={"crash_log": ...})`.
    * **Důsledek:** Plugin `cognitive_reflection.py` (Fáze 3) se přihlásí k odběru této události. Tím získá okamžitý "pohled" na chybu, která způsobila pád, a může okamžitě vytvořit prioritní hypotézu k její opravě.

4.  **Destruktivní Chyba (Rollback)**
    * **Akce:** `guardian.py` bude mít počítadlo (např. 5 pádů během 10 minut).
    * **Akce:** Pokud je tento limit překročen (destruktivní smyčka chyb), `guardian.py` provede:
        1.  Zavolá (přes `subprocess`) `git reset --hard HEAD~1` na větvi `master-sophia` (dle `config/autonomy.yaml`).
        2.  Spustí starší, stabilní verzi Sophii (opět s argumentem `--recovery-from-crash`).
    * **Výsledek:** Starší, stabilní Sophia se spustí a okamžitě dostane log o chybě, kterou udělala její "budoucí" (již smazaná) verze. Může tak analyzovat problém a vyhnout se mu.