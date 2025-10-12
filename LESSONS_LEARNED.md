# Poučení z Vývoje Projektu Nomád

Tento dokument analyzuje evoluční cestu projektu Nomád, identifikuje klíčové architektonické "slepé uličky" a shrnuje poučení, která z nich plynou. Cílem je zabránit opakování minulých chyb v budoucí reimplementaci.

## 1. Architektura "Jednoho Agenta" (Počáteční Stav)

### Popis
Projekt začal s jednoduchou, monolitickou architekturou, kde jediná třída (původní `JulesOrchestrator`) byla zodpovědná za vše: parsování uživatelského vstupu, vedení historie, volání nástrojů a formátování výstupu.

### Problémy a Selhání
- **Nedostatek Specializace:** Jeden agent se snažil být zároveň konverzačním partnerem, plánovačem i vykonavatelem úkolů. To vedlo ke zmateným promptům a neefektivnímu rozhodování.
- **Křehkost:** Jakákoliv změna v logice (např. přidání nového nástroje) mohla neočekávaně ovlivnit všechny ostatní aspekty jeho chování.
- **Špatná Škálovatelnost:** S rostoucí komplexitou úkolů se monolitický design stal neudržitelným. Agent ztrácel kontext v dlouhých konverzacích a nedokázal efektivně rozkládat složité problémy na menší kroky.

## 2. Architektura "Manažer/Worker" (Fáze 1)

### Popis
V reakci na problémy monolitu byla zavedena dvouvrstvá architektura (`ConversationalManager` a `WorkerOrchestrator`), jak je zaznamenáno ve `WORKLOG.md` z 9. října 2025. Cílem bylo oddělit interakci s uživatelem (Manažer) od samotného provádění práce (Worker).

### Problémy a Selhání
- **Halucinace Nástrojů Manažera:** Manažer, ačkoliv neměl přímý přístup k nástrojům, se často snažil "vymýšlet" plán, který zahrnoval konkrétní volání nástrojů. Tento plán pak předal Workerovi, který byl nucen ho slepě následovat, i když byl plán chybný.
- **Rigidní Triage:** Manažer se stal úzkým hrdlem. Jeho snaha o "triáž" (rozhodování, co má Worker dělat) byla neefektivní, protože neměl dostatečný kontext o reálném stavu souborového systému nebo výsledcích předchozích operací.
- **Ztráta Kontextu:** Worker dostával pouze izolované příkazy od Manažera, nikoliv celkový cíl mise. To mu bránilo v inteligentním rozhodování a improvizaci.

## 3. Architektura "Reflektivní Mistr" (Fáze 2)

### Popis
Dalším krokem bylo přidání sebereflexe. Byly zavedeny mechanismy (`ReflectionServer`), které měly agentovi umožnit analyzovat své neúspěchy a poučit se z nich.

### Problémy a Selhání
- **Reflexe bez Kontextu:** Samotná sebereflexe byla neúčinná, protože byla aplikována na již tak chybné a fragmentované architektuře. Agent mohl správně identifikovat, *proč* selhal jeden konkrétní krok, ale toto poučení se nikdy nedostalo zpět k vyšší vrstvě (Manažerovi), která by mohla na jeho základě upravit celkový plán. Reflexe se stala izolovanou akademickou činností bez reálného dopadu na budoucí rozhodování.

## 4. Architektura "Stateful Mission" (Současný Stav)

### Popis
Současná architektura je třívrstvá (`MissionManager`, `ConversationalManager`, `WorkerOrchestrator`).
1.  `MissionManager` přijme cíl, vytvoří hrubý plán (seznam úkolů) a spravuje misi.
2.  `ConversationalManager` přijme jeden úkol z plánu a předá ho Workerovi. Je to v podstatě jen další mezivrstva.
3.  `WorkerOrchestrator` přijme konkrétní úkol, provede ho pomocí nástrojů a vrátí výsledek.

### Problémy a Selhání
- **Architektonická Schizofrenie:** Projekt trpí "roztrojenou osobností". Každá vrstva má vlastní zodpovědnost, vlastní historii a vlastní "pohled na svět". Neexistuje žádný jediný, koherentní "mozek".
- **Fragmentace Kontextu:** Toto je nejzávažnější problém. `MissionManager` zná celkový cíl, ale nezná detaily exekuce. `WorkerOrchestrator` zná detaily exekuce, ale nezná celkový cíl. `ConversationalManager` je jen neefektivní pošťák mezi nimi.
- **Kritická Chyba v Učení (`KeyError` Koncept):** Agent se nemůže efektivně poučit z vlastních chyb. Když `MissionManager` na konci mise provede finální reflexi a uloží "poučení" do dlouhodobé paměti (`worker.ltm.add`), toto poučení je k dispozici pouze `WorkerOrchestratorovi` v jeho *dalším* úkolu. Samotný `MissionManager`, který je zodpovědný za plánování, k těmto poučením při tvorbě *nového* plánu nikdy nepřistupuje. Systém si tak usekává zpětnovazební smyčku. Je to ekvivalent `KeyError`, kde se jedna část mozku snaží získat vzpomínku, kterou uložila jiná část, ale hledá ji na špatném místě.

## 5. Závěr: Hlavní Ponaučení

Hlavním nepřítelem projektu Nomád nebyla specifická technologie, ale **přílišná a neustále rostoucí komplexnost**. Každá nová architektonická vrstva byla zavedena ve snaze vyřešit problémy té předchozí, ale ve skutečnosti jen přidala další švy, přes které unikal kontext. Snaha řešit problém ztráty kontextu přidáváním dalších manažerů a vrstev je slepá ulička, která problém paradoxně zhoršuje.

**Finální poučení zní: Jediná cesta vpřed vede skrze radikální zjednodušení.** Je nutné opustit model více vrstev a vrátit se k konceptu jediného, koherentního "mozku", který však bude navržen jako robustní stavový stroj, aby se předešlo chybám původní monolitické architektury.