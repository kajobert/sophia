# Návrh Implementace: Fáze 2 - Reflektivní Mistr

**Cíl:** Naučit agenta Nomáda, aby se aktivně poučil ze svých předchozích akcí. Po dokončení této fáze bude Nomád schopen analyzovat svůj výkon, identifikovat neefektivní postupy a tyto poznatky aplikovat v budoucích úkolech.

---

## 1. Mechanismus Sebereflexe

**Problém:** Nomád opakuje stejné, i když neefektivní, postupy, protože nemá mechanismus, jak zhodnotit svůj výkon.

**Navrhované Řešení:** Po každém dokončeném úkolu (ať už úspěšně, nebo neúspěšně) spustí `ConversationalManager` nový proces "sebereflexe".

**Změny v Kódu:**
-   `core/conversational_manager.py`:
    -   Po obdržení finálního výsledku od `WorkerOrchestrator` zavolá novou metodu `_run_reflection(task_history)`.
    -   Tato metoda vezme historii kroků daného úkolu, vloží ji do nového promptu (`reflection_prompt.txt`) a zavolá LLM.
    -   Výsledný "poznatek" (např. "Pro vytvoření adresáře není potřeba komplexní plán, stačí jeden `mkdir` příkaz.") uloží do dlouhodobé paměti (LTM) se speciálním metadatem, např. `{"type": "learning"}`.

**Nový Prompt (`prompts/reflection_prompt.txt`):**
-   Bude obsahovat instrukce jako: "Jsi zkušený softwarový architekt. Níže je záznam práce AI agenta na daném úkolu. Analyzuj tento postup. Byl efektivní? Co se dalo udělat lépe? Zformuluj jeden krátký, jasný poznatek, který by agentovi pomohl příště vyřešit podobný úkol lépe."

---

## 2. Aplikace Získaných Znalostí

**Problém:** I kdyby Nomád měl poznatky v paměti, neví, jak je použít.

**Navrhované Řešení:** Musíme zajistit, aby se relevantní "poučení" z LTM stala součástí kontextu, který `WorkerOrchestrator` používá při rozhodování.

**Změny v Kódu:**
-   `core/prompt_builder.py`:
    -   Metoda `build_prompt` bude upravena. Kromě standardního prohledávání LTM na základě popisu úkolu provede i druhé, cílené prohledávání s dotazem specificky na "poučení".
    -   Nalezené poznatky vloží do systémového promptu ve speciální sekci, např.:
        ```
        # **POUČENÍ Z MINULÝCH ÚKOLŮ**
        - Pro vytvoření adresáře stačí jeden `mkdir` příkaz.
        - Před čtením souboru je dobré ověřit jeho existenci pomocí `list_files`.
        ```

---

## 3. Testování a Ověření Fáze 2

**Cíl:** Ověřit, že učící cyklus funguje.

**Testovací Scénář:**
1.  **První Pokus:** Zadáme Nomádovi úkol, který v minulosti řešil neefektivně (např. "vytvoř adresář `temp_test`"). Budeme sledovat, zda opět použije zbytečně složitý postup.
2.  **Kontrola Reflexe:** Ověříme, že po dokončení úkolu byl do LTM uložen nový, správný poznatek (např. "vytvoření adresáře je jednoduchý příkaz").
3.  **Druhý Pokus:** Zadáme velmi podobný úkol ("vytvoř adresář `temp_test_2`").
4.  **Ověření Zlepšení:** Budeme sledovat, zda Nomád tentokrát použije zjednodušený postup na základě nově nabyté znalosti. Úspěchem je, pokud úkol vyřeší výrazně rychleji a s menším počtem kroků.