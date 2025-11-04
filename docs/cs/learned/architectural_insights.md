# Architektonické Poznatky z Archivů Sophie

Tento dokument analyzuje tři odlišné architektonické paradigmy objevené v archivech Sophie. Každý z nich představuje odlišnou filozofii pro budování autonomního agenta a nabízí cenné lekce pro náš současný model Core-Plugin.

---

## 1. Proaktivní Stavový Automat (`archive/nomad-archived`)

Tato architektura byla postavena kolem centrálního orchestrátoru (`NomadOrchestratorV2`), který fungoval jako jednoduchý, ale výkonný stavový automat.

*   **Základní Koncept:** Nepřetržitá smyčka mezi třemi stavy: `THINKING` (Přemýšlení), `EXECUTING_TOOL` (Vykonávání Nástroje) a `HANDLING_ERROR` (Zpracování Chyby). Inteligence agenta byla soustředěna v jeho schopnosti rozhodnout o *nejlepším dalším kroku* ve stavu `THINKING`, což z něj činilo "proaktivní", nikoli předem naplánovaný systém.

*   **Klíčové Komponenty:**
    *   **Orchestrátor:** Monolitická třída, která držela stav, historii a hlavní prováděcí smyčku.
    *   **MCPClient:** Klient pro volání nástrojů, které byly koncipovány jako samostatné, běžící procesy. Jednalo se o primitivní formu pluginového systému.

*   **Silné Stránky:**
    *   **Robustnost:** Dedikovaný stav pro zpracování chyb činí systém odolným.
    *   **Srozumitelnost:** Logika je snadno sledovatelná, což usnadňuje ladění.
    *   **Efektivita:** Model "nejlepšího dalšího kroku" je flexibilní a dokáže se přizpůsobit neočekávaným výsledkům bez křehkého, více krokového plánu.

*   **Slabé Stránky:**
    *   **Monolitický Design:** Jádrová logika je pevně svázána v rámci orchestrátoru. Rozšíření by vyžadovalo úpravu této základní třídy.
    *   **Omezená Abstrakce:** Systém přemýšlí v termínech "volání nástrojů", nikoli ve vyšších konceptech. Chybí mu hlubší model uvažování.

*   **Ponaučení pro Současnou Architekturu:** Logika stavového automatu je vynikajícím modelem pro `ConsciousnessLoop` v našem `core/kernel.py`. Koncept proaktivní, jednokrokové rozhodovací smyčky je silný a osvědčený vzor.

---

## 2. Hierarchická Kognitivní Architektura (HCA) (`archive/sophia-archived`)

Tato architektura představuje radikální posun k abstraktnějšímu, bio-inspirovanému modelu kognice.

*   **Základní Koncept:** Systém je rozdělen do tří vrstev, které modelují evoluční vývoj mozku:
    1.  **Plazí Mozek (Instinkty):** Rychlé, reflexivní filtrování a kontrola na základě pravidel.
    2.  **Savčí Mozek (Podvědomí):** Obohacení kontextu, rozpoznávání vzorů a načítání z dlouhodobé paměti.
    3.  **Neokortex (Vědomí):** Strategické plánování, uvažování a konečné rozhodování.

*   **Silné Stránky:**
    *   **Oddělení Zodpovědností (Separation of Concerns):** Brilantní model pro oddělení různých typů "myšlení".
    *   **Koncepční Hloubka:** Poskytuje bohatý slovník pro uvažování o tom, *jak* by měl agent myslet, nejen co by měl *dělat*.
    *   **Škálovatelnost:** Různé vrstvy by mohly být škálovány nebo vyvíjeny nezávisle.

*   **Slabé Stránky:**
    *   **Složitost Implementace:** Převést tyto abstraktní koncepty do funkčního kódu je značná výzva.
    *   **Potenciální Úzká Hrdla (Bottlenecks):** Striktní hierarchický tok informací by mohl vytvářet problémy s výkonem.

*   **Ponaučení pro Současnou Architekturu:** HCA poskytuje silný mentální model pro kategorizaci a navrhování našich pluginů. Můžeme o pluginech přemýšlet jako o příslušnících různých "kognitivních vrstev", což může vést jejich design a interakci. Například plugin pro validaci bezpečnosti je "plazí", zatímco komplexní plugin pro generování kódu je "neokortex".

---

## 3. Prototyp Založený na Frameworku (`archive/sophia-old-archived`)

Tato nejranější verze byla postavena s využitím frameworku pro orchestraci agentů `CrewAI`.

*   **Základní Koncept:** Využít existující framework na vysoké úrovni k rychlému vytvoření funkčního systému s více agenty. Klíčovou inovací byl proces "snění".

*   **Klíčové Komponenty:**
    *   **CrewAI:** Zajišťoval základní životní cyklus agenta, provádění nástrojů a komunikaci mezi agenty.
    *   **Paměťový Agent ("Snění"):** Specializovaný agent, který se spouští po interakci, aby analyzoval krátkodobou paměť a konsolidoval klíčové poznatky do dlouhodobého vektorového úložiště ChromaDB.

*   **Silné Stránky:**
    *   **Rychlý Vývoj:** Použití frameworku umožnilo velmi rychlou cestu k funkčnímu prototypu.
    *   **Autonomní Učení:** Koncept "snění" je silné a elegantní řešení pro budování sémantické znalostní báze v průběhu času.

*   **Slabé Stránky:**
    *   **Závislost na Frameworku:** Architektura je omezena designovými rozhodnutími CrewAI.
    *   **Méně Kontroly:** Menší flexibilita při přizpůsobování základního životního cyklu agenta ve srovnání se systémem vytvořeným na míru.

*   **Ponaučení pro Současnou Architekturu:** Proces "snění" je fantastický koncept pro budoucí, pokročilou verzi našeho pluginu `memory_chroma`. Poskytuje model, jak může agent autonomně spravovat svou vlastní dlouhodobou paměť.
