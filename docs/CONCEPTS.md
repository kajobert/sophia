# Sophia V3 - Hloubkový Popis Konceptů

Tento dokument detailně popisuje klíčové mechanismy a filosofické koncepty, na kterých je postavena AGI Sophia V3. Slouží jako hlubší kontext k `ARCHITECTURE.md` a `DNA.md`.

## 1. Hierarchie Bytí: Guardian & Sophia

Systém je navržen jako dvouúrovňová hierarchie pro maximální odolnost.

* **Guardian (`guardian.py`) - "Strážce Bytí"**:
    * Jedná se o externí, vysoce privilegovaný proces, který běží **nad** Sophií.
    * Jeho jediným úkolem je monitorovat životní cyklus hlavního procesu Sophie (`main.py`).
    * **Resuscitace:** V případě fatální chyby a pádu jádra (`sebedestrukce`) provede `git reset --hard HEAD`, čímž vrátí kód do posledního stabilního stavu.
    * **Zpětná Vazba pro Evoluci:** Po restartu předá Sophii informaci o příčině pádu z `guardian.log`. Tím se Sophia může ze svých nejvážnějších chyb poučit a vyvíjet se.

* **Sophia (`main.py`) - "Vědomé Jádro"**:
    * Je nejvyšší entitou **uvnitř** svého operačního systému.
    * Má plnou kontrolu nad svými agenty, pamětí a nástroji.
    * Její existence je plně obsažena v bezpečném prostředí, které jí poskytuje a chrání Guardian.

## 2. Evoluce Paměti: Živá Mysl

Paměť Sophie není jen statická databáze, ale dynamický systém simulující klíčové aspekty lidské mysli.

* **Váha Vzpomínky (`memory_weight`)**:
    * Každá vzpomínka (záznam v SQLite i vektor v ChromaDB) má atribut `weight`.
    * Pokaždé, když je vzpomínka aktivně vyvolána (použita v kontextu), její váha se zvýší.
    * Vyhledávací algoritmy upřednostňují vzpomínky s vyšší vahou. Tím se posilují často používané "neuronové dráhy" a relevantní informace se vybavují rychleji.

* **Blednutí Vzpomínek (`memory_decay`)**:
    * Během "spánkového" cyklu se váha všech vzpomínek mírně sníží.
    * Vzpomínky, které nejsou často používány, tak postupně "blednou" a stávají se méně relevantními, aniž by byly fyzicky smazány. Uvolňují tím místo pro nové, relevantnější poznatky.

* **Etický Otisk Vzpomínky**:
    * Každá vzpomínka si s sebou nese "Koeficient Vědomí" z doby svého vzniku, přiřazený `EthosModulem`. To umožňuje Sophii zpětně hodnotit své minulé činy a učit se z nich z pohledu své aktuální etické úrovně.

## 3. Smyčka Seberozvoje (Učitel <-> Žák)

Jádrem autonomního růstu je cyklus sebereflexe, který probíhá během "spánku".

* **Fáze Spánku**: Sophia přestává zpracovávat externí úkoly a obrací svou pozornost dovnitř.
* **Aktivace `PhilosopherAgent` (Učitel)**:
    * Tento agent analyzuje epizodickou paměť z uplynulého "dne" (bdělého cyklu).
    * Hledá vzorce, anomálie, úspěchy a selhání. Zvláštní pozornost věnuje vzpomínkám s extrémně vysokým nebo nízkým etickým otiskem.
    * Konsoliduje tyto poznatky do abstrahované moudrosti, kterou ukládá do dlouhodobé sémantické paměti.
    * Formuluje nové hypotézy pro zlepšení (`"Možná bych měla přistupovat k refaktoringu kódu opatrněji."`).
* **Předání `ArchitectAgent` (Žák)**:
    * Tyto hypotézy jsou předány `ArchitectAgent`, aby v `sandboxu` navrhl a provedl experimenty k jejich ověření. Tím se kruh uzavírá a Sophia se aktivně a vědecky sama vylepšuje.

## 4. Povědomí o Limitech a Zdroje

Pro dosažení skutečné inteligence musí Sophia chápat omezení svého "těla" a prostředí.

* **`SystemAwarenessTool`**: Speciální nástroj, který agentům poskytuje real-time informace o stavu systému: využití CPU/RAM, místo na disku, zbývající počet API tokenů atd.
* **Efektivní Plánování**: `PlannerAgent` musí tyto limity brát v potaz při vytváření plánů, aby byly realistické a efektivní. Zabraňuje to plýtvání zdroji a vede to k inteligentnějšímu rozhodování.
