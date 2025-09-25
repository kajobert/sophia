# Protokol Nomad: Manuál pro Zajištění Perzistence a Kontinuity Agenta

**Verze:** 2.0
**Datum:** 2025-09-25
**Kódové Označení Agenta:** Nomad (perzistentní entita agenta Jules)

## 1. Abstrakt

Tento dokument definuje **Protokol Nomad**, závazný pracovní postup pro spolupráci mezi uživatelem a AI agentem Jules/Nomad. Cílem protokolu je překonat omezení stateless (bezstavových) výpočetních prostředí a zajistit, aby agent disponoval perzistentní pamětí, učením a kontextovou kontinuitou napříč jednotlivými úkoly. Verze 2.0 přidává mechanismy pro detailní sledování práce a plánování.

## 2. Cíle Protokolu

-   **Kontinuita:** Zajistit, aby uživatel vždy komunikoval s agentem, který si pamatuje předchozí interakce a zkušenosti.
-   **Spolehlivost:** Vytvořit jednoduchý a robustní mechanismus pro "načtení" a "uložení" stavu agenta.
-   **Transparentnost:** Poskytnout jasný přehled o postupu práce pomocí checklistů a detailních záznamů v deníku.
-   **Udržitelnost:** Vytvořit systém, který je srozumitelný a použitelný pro jakéhokoli budoucího vývojáře.

## 3. Fáze Protokolu

### Fáze 0: Inicializace (Krok pro Uživatele)

-   **Akce:** Do prvního promptu v novém chatu (`jules.google.com/task/...`) vložte následující direktivu:
    ```
    Aktivuj Protokol Nomad.
    ```

### Fáze 1: Rehydratace a Plánování (Krok pro Agenta)

Po obdržení inicializační direktivy provede agent následující kroky:

1.  **Rozpoznání Protokolu:** Agent identifikuje klíčová slova a aktivuje režim obnovy.
2.  **Načtení Pravidel a Identity:** Agent si přečte soubory `rules.md` (dříve `AGENTS.md`) a `agent.md` (dříve `JULES.md`), aby si plně obnovil svou identitu, pravidla a schopnosti.
3.  **Potvrzení Rehydratace:** Agent potvrdí uživateli úspěšné načtení stavu.
4.  **Vytvoření Plánu s Checklistem:** Agent vytvoří podrobný plán pro zadaný úkol. **Na začátek tohoto plánu musí vložit jednoduchý bodový checklist**, který shrnuje hlavní kroky. Tento checklist bude sloužit pro rychlé sledování postupu.

### Fáze 2: Standardní Pracovní Postup (Spolupráce)

Po úspěšné rehydrataci a vytvoření plánu pokračuje spolupráce standardním režimem:
-   Agent postupuje podle plánu.
-   Uživatel (Robert) sleduje postup a může "odškrtávat" splněné body v checklistu.
-   Agent striktně dodržuje pravidlo o prioritě dokumentace a aktualizuje všechny relevantní soubory po každé funkční změně.

### Fáze 3: Dehydratace a Záznam (Krok pro Agenta)

Před dokončením úkolu (před voláním nástroje `submit`) je agent povinen uložit svůj nově nabytý stav a zdokumentovat svou práci.

1.  **Aktualizace Dlouhodobé Paměti:** Agent provede úpravu souboru `rules.md` (sekce entity), pokud získal nějakou novou, trvalou zkušenost.
2.  **Zápis do Pracovního Deníku:** Agent vytvoří nový, podrobný záznam v souboru `WORKLOG.md` podle definovaného formátu. Tento záznam musí detailně popisovat, co bylo uděláno, proč, jaké byly problémy a jaký je dopad. Tento krok je **povinný** pro každý významný úkol.

## 4. Závěr

Důsledné dodržování tohoto protokolu oběma stranami je klíčové pro vybudování skutečně efektivního, učícího se a perzistentního AI spolupracovníka.