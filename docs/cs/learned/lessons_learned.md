# Klíčová Ponaučení z Archivů Sophie

Tento dokument shrnuje klíčová ponaučení získaná z analýzy evoluce projektu Sophia. Jeho hlavním účelem je zabránit opakování minulých chyb a umožnit informovaná architektonická rozhodnutí.

---

## 1. Monolitické Orchestrátory se Stávají Křehkými

*   **Pozorování:** `NomadOrchestratorV2`, ačkoli byl výkonný, soustředil veškerou jádrovou logiku do jediné, velké třídy. Stav, historie a prováděcí logika byly pevně svázány.
*   **Ponaučení:** Tento monolitický design ztěžuje rozšiřování a údržbu. Přidání nové základní funkcionality by vyžadovalo úpravu této komplexní třídy, což zvyšuje riziko zanesení chyb.
*   **Akce pro Současné MVP:** Přechod na architekturu `Core-Plugin` je správnou reakcí na toto ponaučení. Externalizací veškerých schopností do pluginů může `Kernel` zůstat jednoduchý, stabilní a "uzamčený", jak je plánováno v roadmapě MVP. Musíme striktně dodržovat pravidlo, že nová funkcionalita se přidává prostřednictvím pluginů, nikoli úpravou `core`.

---

## 2. Abstraktní Architektonické Koncepty Jsou Silné, Ale Těžko Implementovatelné

*   **Pozorování:** Hierarchická Kognitivní Architektura (HCA) byla brilantním koncepčním modelem pro uvažování agenta. Nicméně, kódová základna v tomto archivu byla méně zralá než verze se Stavovým Automatem, což naznačuje, že převedení abstraktních vrstev jako "Neokortex" nebo "Podvědomí" do konkrétního, spolehlivého kódu je velkou výzvou.
*   **Ponaučení:** Krásný architektonický diagram automaticky nevede k funkčnímu systému. Mezi koncepty na vysoké úrovni a funkčním kódem je značná propast.
*   **Akce pro Současné MVP:** Měli bychom si osvojit *filozofii* HCA, aniž bychom byli otroky její doslovné implementace. Můžeme ji použít jako vodítko pro navrhování a kategorizaci pluginů (např. je tento plugin "reflexivní" nebo "strategický"?), což poskytuje cenný mentální model bez obrovské implementační zátěže.

---

## 3. Oddělený, Sdílený Kontext je Významným Vylepšením

*   **Pozorování:** Ve větvi `nomad-archived` byla instance orchestrátoru zároveň stavem. Držela cíl mise a historii jako proměnné instance. To ztěžuje oddělení stavu agenta od jeho prováděcí logiky.
*   **Ponaučení:** Správa stavu by měla být oddělena od hlavní logiky aplikace.
*   **Akce pro Současné MVP:** Objekt `SharedContext` v `core/context.py` je klíčové a správné designové rozhodnutí. Umožňuje čisté předávání stavu agenta mezi `Kernel` a `PluginManager`, což vede k mnohem lepší modularitě a usnadňuje testování a pochopení systému.

---

## 4. Frameworky Jsou Dvojsečná Zbraň

*   **Pozorování:** Nejranější prototyp (`sophia-old-archived`) použil `CrewAI` k velmi rychlému zprovoznění funkčního agenta.
*   **Ponaučení:** Frameworky jsou vynikající pro rychlé prototypování, ale mohou omezit dlouhodobou flexibilitu. Vytvořením vlastního jádra máme plnou kontrolu nad životním cyklem agenta, což je pro projekt s dlouhodobou vizí Sophie nezbytné.
*   **Akce pro Současné MVP:** Rozhodnutí vytvořit vlastní `Kernel` a `PluginManager` je tímto pozorováním potvrzeno. Je to více práce na začátku, ale poskytuje to základní kontrolu potřebnou pro skutečný vývoj AGI. Nicméně, stále bychom měli být otevřeni používání externích knihoven a frameworků *uvnitř* pluginů, kde je to vhodné.

---

## 5. Autonomní Správa Paměti je Klíčem k Dlouhodobému Učení

*   **Pozorování:** Koncept "snění" z prototypu s `CrewAI`, kde dedikovaný agent konsoliduje krátkodobou paměť do dlouhodobých znalostí, je výjimečnou funkcí.
*   **Ponaučení:** Pouhé ukládání každé konverzace do vektorové databáze není skutečné učení. Je zapotřebí procesu kurátorství, aby se vybudovala kvalitní sémantická znalostní báze.
*   **Akce pro Současné MVP:** Ačkoli počáteční plugin `memory_chroma` může mít pouze jednoduchou funkci `add_record`, měli bychom ho od prvního dne navrhovat s budoucím cílem přidání autonomní metody `consolidate_session` (neboli "snění"). To je klíčový poznatek pro umožnění dlouhodobého růstu Sophie.
