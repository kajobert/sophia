# Roadmapa 04: Autonomní Operace

**Cíl Fáze:** Dosáhnout konečné vize projektu: umožnit Sophii, aby si sama řídila svůj vlastní vývojový cyklus. Tato fáze zahrnuje vytvoření hlavního kognitivního pluginu, který využívá všechny dříve vyvinuté nástroje a analytické schopnosti k delegování úkolů, revizi výsledků a integraci nové funkcionality do svého vlastního systému.

Detailní implementační plán pro tuto fázi je poslední hranicí a bude vytvořen po úspěšném dokončení Rámce pro Sebe-Analýzu.

---

### Implementační Průvodce: Dynamický Kognitivní Engine V3

**Autor:** Gemini & Robert Kajzer
**Datum:** 30. 10. 2025
**Cíl:** Vylepšit kognitivní jádro Sophie o schopnost hierarchického plánování, dynamického přeplánování a vnitřního "myšlení", což povede k robustnějšímu a skutečně adaptivnímu agentovi.

Tento dokument popisuje přechod na pokročilejší model, který se skládá ze tří pilířů.

#### 1. Klíčové Koncepty a Filozofie

**A. Hierarchické Plánování (Hierarchical Planning)**

Místo jediného, monolitického seznamu kroků bude systém pracovat s hierarchií. Udržuje si povědomí o hlavním cíli (např. "analyzuj a reportuj stav projektu") a zároveň se soustředí na provádění dílčího pod-plánu (např. "krok 1: vypiš soubory, krok 2: přečti soubor X"). To nám umožňuje v případě selhání opravit jen malou část, aniž bychom ztratili celkový kontext.

**B. Dynamické Přeplánování (Dynamic Replanning)**

Exekutor (Kernel) se stává chytřejším. Místo slepého provádění plánu nyní postupuje krok za krokem. Po každém kroku zanalyzuje výsledek. Pokud krok selže nebo vrátí neočekávaný výstup, Exekutor okamžitě zastaví, zahodí neplatný pod-plán a požádá Plánovač o vytvoření nového pod-plánu pro splnění hlavního cíle s přihlédnutím k nové situaci (včetně informace o chybě).

**C. Vnitřní Myšlení (Internal Monologue)**

Sophia se učí, že nemusí pro každou operaci volat externí nástroj. Uvědomuje si, že může použít svůj vlastní "mozek" (tool_llm) jako jeden z kroků v plánu. To jí umožňuje provádět transformace dat, sumarizace nebo jakékoliv jiné jazykové operace "v hlavě" jako součást komplexnějšího úkolu.

#### 2. Architektonické Změny

Většina změn se odehraje v srdci systému – v `core/kernel.py` a ve způsobu, jakým pracujeme s kontextem a plánem.

**2.1. Rozšíření `SharedContext` (`core/context.py`)**

Aktuální `SharedContext` je skvělý pro jeden cyklus, ale pro udržení dlouhodobějšího cíle ho musíme mírně rozšířit. Potřebujeme oddělit hlavní cíl od aktuálně prováděného plánu.

*   `main_goal: Optional[str] = None`
*   `current_plan: Optional[List[Dict]] = None`

*Poznámka: Alternativně může `main_goal` zůstat v `user_input` a `current_plan` nahradí stávající `payload['plan']`.*

**2.2. Refaktor Exekutoru (`consciousness_loop` v `core/kernel.py`)**

Hlavní smyčka už nebude iterovat přes všechny kroky plánu. Její logika bude zjednodušena na "cyklus jednoho kroku":

1.  **Získání Cíle:** Na začátku cyklu (pokud není žádný `main_goal`) získá vstup od uživatele a nastaví ho jako `main_goal`.
2.  **Plánování (pokud je potřeba):** Pokud je `current_plan` prázdný, ale `main_goal` existuje, zavolá `cognitive_planner`, aby vytvořil nový plán pro splnění cíle.
3.  **Provedení Jednoho Kroku:** Vezme pouze první krok z `current_plan`.
4.  **Validace a Oprava Argumentů:** Provede stávající "Validation & Repair Loop" jen pro tento jeden krok.
5.  **Spuštění Nástroje:** Zavolá příslušný nástroj (např. `tool_file_system.read_file`).
6.  **Analýza Výsledku:** Zkontroluje výsledek kroku.
    *   **ÚSPĚCH:** Zapíše výsledek do `step_outputs` (jako doposud), odstraní provedený krok z `current_plan` (`current_plan.pop(0)`) a pokračuje do další iterace smyčky.
    *   **SELHÁNÍ:**
        *   Zapíše informaci o selhání do `history` (např. "Krok 'read_file' selhal: Soubor nenalezen.").
        *   Smaže celý `current_plan`.
        *   Smyčka se vrací na začátek, kde v bodě 2. znovu zavolá Plánovač, aby vytvořil nový plán s přihlédnutím k nové informaci o chybě v `history`.

#### 3. Průvodce Implementací (Mise pro Julese)

Toto je krok-za-krokem plán pro implementaci Dynamického Kognitivního Enginu.

**Mise:** Implementace Hierarchického a Dynamického Plánování (V3)
**Agent:** Jules
**Status:** PŘIPRAVENO

1.  **Plán Implementace:**
    *   **Krok 1: Aktualizace Datové Struktury**
        *   V `core/context.py` uprav `SharedContext`, aby lépe reprezentoval `main_goal` a `current_plan`.
    *   **Krok 2: Refaktor `consciousness_loop` na Cyklus Jednoho Kroku**
        *   V `core/kernel.py` přepiš `EXECUTING` fázi. Místo `for step in plan:` použij logiku, která zpracuje jen `plan[0]`.
        *   Ujisti se, že zbytek smyčky (jako Validation & Repair) pracuje s tímto jediným krokem.
    *   **Krok 3: Implementace Smyčky Přeplánování (Replanning Loop)**
        *   Přidej do `consciousness_loop` logiku pro detekci chyby po provedení kroku (např. kontrolou `try...except` bloku nebo návratové hodnoty).
        *   V případě chyby implementuj logiku pro:
            *   Zápis chyby do `context.history`.
            *   Vymazání `context.current_plan`.
            *   Nech smyčku přirozeně pokračovat, což automaticky spustí `cognitive_planner` v další iteraci.
    *   **Krok 4: Vylepšení Promptu Plánovače**
        *   Uprav soubor `config/prompts/planner_prompt_template.txt`.
        *   Přidej instrukce, které explicitně vybízejí LLM, aby použil `tool_llm.execute` pro úkoly jako je formátování, sumarizace nebo transformace dat, pokud pro ně neexistuje jiný specifický nástroj.
        *   Přidej příklad, který ukazuje `tool_llm` jako mezikrok.
    *   **Krok 5: Ověření Pomocí Benchmarku**
        *   Vytvoř nový testovací scénář (benchmark), který ověří všechny nové schopnosti najednou.
        *   **Scénář:** "Vypiš obsah adresáře /, vezmi tento seznam, přeformátuj ho pomocí LLM na očíslovaný seznam, a pokus se výsledek zapsat do souboru `/non_existent_dir/output.txt`."
        *   **Očekávané Chování:**
            1.  Sophia vytvoří plán: `list_directory` -> `tool_llm.execute` -> `write_file`.
            2.  `list_directory` a `tool_llm.execute` proběhnou úspěšně.
            3.  `write_file` selže, protože adresář neexistuje.
            4.  Kernel chybu zaznamená a spustí přeplánování.
            5.  Plánovač vytvoří nový plán, který může vypadat takto: "Vytvoř adresář `/non_existent_dir`" a poté "Zapiš výsledek do `/non_existent_dir/output.txt`".
            6.  Nový plán je úspěšně dokončen.

#### 4. Očekávaný Výsledek

*   Sophia je schopna řešit komplexní, více-krokové úkoly, které vyžadují jak externí nástroje, tak interní "myšlenkové" kroky.
*   Sophia se dokáže zotavit z chyb při provádění jednotlivých kroků, aniž by ztratila povědomí o hlavním cíli, a adaptivně vytvoří nový plán k jeho dosažení.
*   Architektura je připravena na budoucí rozšíření o ještě pokročilejší Hierarchical Task Networks (HTN).

---

### Klíčové Cíle:

1.  **Plugin pro Plánování a Delegování Úkolů (`cognitive_overseer`):**
    *   **Účel:** Hlavní plugin, který orchestruje autonomní vývoj Sophie.
    *   **Základní Schopnosti:**
        *   `formulate_plan`: Analyzovat cíl na vysoké úrovni (např. z `roberts-notes.txt`) a vytvořit detailní, krok-za-krokem implementační plán.
        *   `delegate_task`: Komunikovat s externím API AI programátora ("Jules API") a zadat konkrétní, dobře definovaný kódovací úkol.
        *   `monitor_progress`: Periodicky kontrolovat stav delegovaného úkolu.

2.  **Plugin pro Revizi a Ověřování Kódu (`cognitive_quality_assurance`):**
    *   **Účel:** Umožnit Sophii revidovat a ověřovat kód vytvořený externím AI programátorem.
    *   **Základní Schopnosti:**
        *   `review_code_changes`: Použít nástroje pro sebe-analýzu k zajištění, že nový kód dodržuje všechny vývojářské směrnice.
        *   `run_verification_tests`: Spustit testy spojené s novým kódem k potvrzení funkčnosti.
        *   `provide_feedback`: Požádat o revize od externího programátora, pokud kód není uspokojivý.

3.  **Plugin pro Integraci a Nasazení (`cognitive_integrator`):**
    *   **Účel:** Umožnit Sophii bezpečně integrovat a nasadit schválený nový kód do svého vlastního systému.
    *   **Základní Schopnosti:**
        *   `merge_code`: Použít Git plugin ke sloučení nové feature větve do `develop`.
        *   `update_documentation`: Automaticky aktualizovat `PROJECT_STRUCTURE.md` a další relevantní dokumenty.
        *   `trigger_reload`: Dát pokyn Jádru, aby znovu načetlo registr pluginů a aktivovalo tak novou funkcionalitu.

---

**Kritéria Úspěchu:** Vedoucí projektu může napsat jediný řádek do `roberts-notes.txt`, například: "Vytvoř plugin, který dokáže překládat text pomocí externího API." Sophia je poté z vlastní iniciativy schopna naplánovat úkol, delegovat kódování externímu agentovi, zrevidovat kód, schválit ho a integrovat nový, funkční překladový plugin do svého systému bez jakéhokoli dalšího lidského zásahu.
