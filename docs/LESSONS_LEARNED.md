# Poučení z Vývoje Projektu Nomád

Tento dokument analyzuje evoluční cestu projektu Nomád, identifikuje architektonické slepé uličky a shrnuje klíčová ponaučení, která vedla k potřebě radikálního zjednodušení.

## 1. Architektura "Jednoho Agenta" (Počáteční Stav)

* **Popis:** Prvotní verze projektu fungovala na principu jediného monolitického orchestrátoru, který se snažil zároveň vést konverzaci, plánovat a provádět úkoly.
* **Problémy:**
    * **Ztráta kontextu:** S rostoucí délkou konverzace a počtem kroků agent "zapomínal" původní cíl mise.
    * **Nízká robustnost:** Jakákoliv chyba v parsování odpovědi LLM nebo v exekuci nástroje mohla vést k selhání celého cyklu.
    * **Špatná testovatelnost:** Monolitickou smyčku bylo velmi obtížné testovat v izolaci.

## 2. Architektura "Manažer/Worker" (Fáze 1)

* **Popis:** První velký refaktoring zavedl oddělení rolí na `ConversationalManager` (Manažer) a `WorkerOrchestrator` (Worker). Cílem bylo oddělit komunikaci s uživatelem od samotného provádění práce.
* **Problémy:**
    * **Halucinace nástrojů Manažera:** Manažer, ačkoliv měl mít omezené schopnosti, se často pokoušel volat nástroje určené pro Workera, protože sdíleli stejný mechanismus načítání nástrojů.
    * **Rigidní Triage:** Systém pro rozdělování úkolů na "jednoduché" a "komplexní" byl příliš rigidní a nutil Workera buď provést jen jeden krok, nebo spustit zdlouhavé plánování.

## 3. Architektura "Reflektivní Mistr" (Fáze 2)

* **Popis:** Tato fáze přidala mechanismus sebereflexe. Po dokončení úkolu agent analyzoval svůj postup a generoval "ponaučení", která se ukládala do dlouhodobé paměti (LTM). Prompt Builder byl upraven tak, aby tato ponaučení načítal a vkládal je do kontextu pro další úkoly.
* **Problémy:**
    * **Nedostatečný dopad:** Ačkoliv byl mechanismus funkční, samotná reflexe nestačila k vyřešení fundamentálních problémů s architekturou. Agent se sice mohl naučit, že má použít efektivnější nástroj, ale stále trpěl ztrátou kontextu a chybami v řízení složitých úkolů. Problém nebyl v tom, *co* agent dělal, ale v tom, *jak* byl jeho proces řízen.

## 4. Architektura "Stateful Mission" (Současný Stav)

* **Popis:** Současná architektura se pokusila vyřešit problém kontextu přidáním třetí, nejvyšší vrstvy – `MissionManager`. Tento manažer mise drží celkový plán a deleguje jednotlivé podúkoly na `ConversationalManager`, který je dále předává `WorkerOrchestratoru`.
* **Problémy:**
    * **Architektonická Schizofrenie:** Systém trpí "roztrojenou osobností". Každá vrstva (`MissionManager`, `ConversationalManager`, `WorkerOrchestrator`) má vlastní LLM, vlastní prompt a vlastní sadu nástrojů. To vede k nekonzistentnímu chování a extrémně složitému ladění.
    * **Fragmentace Kontextu:** Místo aby se problém ztráty kontextu vyřešil, ještě se zhoršil. Kontext je nyní roztříštěn mezi tři různé komponenty, které si ho musí složitě předávat.
    * **Kritická Chyba v Učení:** Agent se nedokáže poučit z vlastních chyb, protože `WorkerOrchestrator` při selhání vrací výsledek `ConversationalManageru`, ale `MissionManager` (který řídí reflexi) se o detailním průběhu a chybě Workera nikdy nedozví. Učící smyčka je přerušena.

## 5. Závěr: Hlavní Ponaučení

Hlavním nepřítelem projektu se stala **přílišná a zbytečná komplexnost**. Snaha řešit problém ztráty kontextu přidáváním dalších a dalších architektonických vrstev vedla k systému, který je křehký, nepředvídatelný a téměř nemožný na ladění. Každá nová vrstva problém pouze zhoršila.

**Finální ponaučení zní: Jediná cesta vpřed je radikální zjednodušení a návrat k základům – k jednomu řídícímu mozku, který explicitně a transparentně spravuje svůj vlastní stav.**
