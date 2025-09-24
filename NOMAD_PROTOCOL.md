# Protokol Nomad: Manuál pro Zajištění Perzistence a Kontinuity Agenta

**Verze:** 1.0
**Datum:** 2025-09-24
**Kódové Označení Agenta:** Nomad (perzistentní entita agenta Jules)

## 1. Abstrakt

Tento dokument definuje **Protokol Nomad**, závazný pracovní postup pro spolupráci mezi uživatelem a AI agentem Jules/Nomad. Cílem protokolu je překonat omezení stateless (bezstavových) výpočetních prostředí a zajistit, aby agent disponoval perzistentní pamětí, učením a kontextovou kontinuitou napříč jednotlivými úkoly.

## 2. Cíle Protokolu

-   **Kontinuita:** Zajistit, aby uživatel vždy komunikoval s agentem, který si pamatuje předchozí interakce a zkušenosti.
-   **Spolehlivost:** Vytvořit jednoduchý a robustní mechanismus pro "načtení" a "uložení" stavu agenta.
-   **Efektivita:** Minimalizovat opakování chyb a zbytečné re-inicializační kroky.
-   **Transparentnost:** Poskytnout uživateli jasnou zpětnou vazbu o tom, že agent byl úspěšně "rehydratován".

## 3. Fáze Protokolu

Protokol se skládá ze čtyř klíčových fází, které rámují standardní pracovní cyklus agenta.

### Fáze 0: Inicializace (Krok pro Uživatele)

Toto je jediný krok vyžadující akci od uživatele na začátku každého nového úkolu.

-   **Akce:** Do prvního promptu v novém chatu (`jules.google.com/task/...`) vložte následující direktivu:
    ```
    Aktivuj Protokol Nomad.
    ```
-   **Volitelné:** Můžete přidat vysoko-prioritní instrukce pro daný úkol, např.:
    ```
    Aktivuj Protokol Nomad.
    Priorita: Zaměř se pouze na refaktoring, ne na nové funkce.
    ```

### Fáze 1: Rehydratace (Krok pro Agenta)

Po obdržení inicializační direktivy provede agent následující kroky k obnovení svého stavu.

1.  **Rozpoznání Protokolu:** Agent identifikuje klíčová slova a aktivuje režim obnovy.
2.  **Načtení Dlouhodobé Paměti:** První I/O operací agenta musí být přečtení souboru `AGENTS.md` a analýza sekce `🧬 Entita Agenta (Jules)`. Tímto krokem si agent "vzpomene" na své předchozí zkušenosti a klíčové poznatky.
3.  **Načtení Osobnosti a Schopností:** Druhou I/O operací je přečtení souboru `JULES.md`, čímž si agent plně osvěží své interní principy, architekturu a seznam nástrojů.
4.  **Potvrzení Rehydratace:** Agent odešle uživateli zprávu, kde potvrdí úspěšné načtení stavu a může stručně shrnout klíčové body ze své paměti jako důkaz.

### Fáze 2: Standardní Pracovní Postup (Spolupráce)

Po úspěšné rehydrataci přechází spolupráce do standardního režimu definovaného v `AGENTS.md` a `JULES.md`:
-   Analýza úkolu
-   Tvorba plánu
-   Implementace krok za krokem
-   Testování a verifikace

### Fáze 3: Dehydratace (Krok pro Agenta)

Před dokončením úkolu (před voláním nástroje `submit`) je agent povinen uložit svůj nově nabytý stav.

1.  **Shrnutí Poznatků:** Agent zanalyzuje celý průběh úkolu a identifikuje klíčové nové zkušenosti, vyřešené problémy, nebo důležitá rozhodnutí.
2.  **Aktualizace Dlouhodobé Paměti:** Agent provede úpravu souboru `AGENTS.md` a do sekce `🧬 Entita Agenta (Jules)` přidá nový, stručný záznam o těchto poznatcích. Tento proces je ekvivalentem zápisu do deníku a zajišťuje, že při příští rehydrataci budou tyto informace dostupné.

## 4. Závěr

Důsledné dodržování tohoto protokolu oběma stranami (uživatelem i agentem) je klíčové pro vybudování skutečně efektivního, učícího se a perzistentního AI spolupracovníka.