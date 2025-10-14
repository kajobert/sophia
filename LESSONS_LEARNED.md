# Poučení z Vývoje Projektu Nomád

Tento dokument analyzuje evoluční cestu projektu Nomád, identifikuje klíčové architektonické chyby a shrnuje ponaučení, která jsou základem pro finální reimplementaci.

## 1. Architektura "Jednoho Agenta" (Počáteční Stav)

*   **Popis:** Projekt začal jako monolitický agent, kde jediná třída zodpovídala za vše: porozumění, plánování, exekuci i komunikaci.
*   **Problémy:**
    *   **Ztráta kontextu:** S rostoucí délkou konverzace se systémový prompt stával přeplněný, což vedlo k "amnézii" a neschopnosti sledovat dlouhodobé cíle.
    *   **Nízká modularita:** Jakákoliv změna v logice vyžadovala úpravu masivní centrální třídy, což zvyšovalo riziko regresí.
    *   **Neefektivní ladění:** Bylo téměř nemožné izolovat a ladit specifické části procesu (např. pouze plánování).

## 2. Architektura "Manažer/Worker" (Fáze 1)

*   **Co řešila:** Snažila se oddělit strategické plánování (Manažer) od exekuce úkolů (Worker). Manažer měl za úkol pouze komunikovat s uživatelem a delegovat technické úkoly Workerovi.
*   **Nový problém - Halucinace nástrojů:** Vznikl kritický problém. Manažer, ačkoliv neměl mít přístup k technickým nástrojům (jako `read_file`), si jejich existenci "halucinoval" a snažil se je volat. To vedlo k neustálým chybám a zacyklení, protože nedokázal pochopit, že jeho rolí je pouze delegovat. Systém se stal rigidním a neschopným se zotavit z tohoto fundamentálního nepochopení rolí.

## 3. Architektura "Reflektivní Mistr" (Fáze 2)

*   **Co řešila:** Přidala nad Manažera další vrstvu ("Mistr"), jejímž jediným úkolem bylo analyzovat chyby a upravovat prompt pro Manažera. Cílem bylo "naučit" Manažera, aby nehalucinoval nástroje.
*   **Proč selhala:** Sebereflexe sama o sobě nestačila. Přidání další vrstvy jen zvýšilo komplexnost. Místo řešení kořenového problému (fragmentace kontextu a rolí) se systém snažil "záplatovat" symptomy. Každá vrstva měla jen část celkového obrazu, což vedlo k ještě většímu zmatení.

## 4. Architektura "Stateful Mission" (Současný Stav)

*   **Popis:** Současná architektura je třívrstvá: `MissionManager` (dlouhodobé mise), `ConversationalManager` (konverzace) a `WorkerOrchestrator` (exekuce). Každá vrstva má vlastní stav a paměť.
*   **Proč selhává - "Architektonická Schizofrenie":**
    *   **Roztrojená Osobnost:** Agent efektivně existuje jako tři oddělené entity. Každá vrstva má jiný pohled na svět, jiné cíle a jiný kontext. Komunikace mezi nimi je neefektivní a ztrátová.
    *   **Fragmentace Kontextu:** Nejdůležitější informace (jako je plán mise nebo výsledek nástroje) jsou roztříštěny mezi tři různé objekty. Žádná část systému nemá kompletní obraz.
    *   **Kritická Chyba `KeyError`:** Agent má mechanismus pro učení se z minulých chyb (`learnings`), ale kvůli fragmentaci kontextu se tato klíčová informace často ztratí při předávání mezi vrstvami. To vede k `KeyError` a brání agentovi v tom nejdůležitějším: poučit se z vlastních chyb. Systém je odsouzen k jejich opakování.

## 5. Závěr: Hlavní Ponaučení

Hlavním nepřítelem projektu nebyla chybějící funkce, ale **přílišná komplexnost**. Každý pokus o řešení problému ztráty kontextu přidáním další architektonické vrstvy problém paradoxně jen zhoršil. Vytvořili jsme systém, který je tak složitý, že mu žádná jeho část nerozumí.

Finální architektura se musí vrátit k základům a soustředit se na **jednoduchost, centralizovaný stav a robustní datové toky**.