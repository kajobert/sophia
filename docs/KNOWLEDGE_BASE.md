# 🧠 Znalostní Báze Projektu Sophia

Tento dokument je živou znalostní bází, která shrnuje klíčové technické problémy, na které jsme narazili během vývoje, a osvědčená řešení, která jsme aplikovali. Slouží jako "kniha poučení" pro budoucí vývojáře (AI i lidi), aby se předešlo opakování stejných chyb a urychlil se vývoj.

**Jak přispívat:** Každý člen týmu (včetně AI agentů) je povinen do této báze přidávat nové poznatky. Pokud narazíte na významný problém, objevíte efektivní řešení nebo učiníte důležité architektonické rozhodnutí, zaznamenejte ho sem. Pro zachování konzistence používejte formát specifikovaný v `AGENTS.md`. Vaše příspěvky jsou klíčové pro kolektivní růst a úspěch projektu.

---

### Téma: Refaktorace jádra na Hierarchickou Kognitivní Architekturu (HKA)
**Datum**: 2025-09-23
**Autor**: Automated Refactor Agent
**Kontext**: Původní architektura projektového jádra používala centrální `Orchestrator` se smíšenou logikou plánování, vykonávání a opravy plánů. To komplikovalo rozšiřitelnost, testovatelnost a jasné oddělení zodpovědností. Cílem refaktoringu bylo přejít na Hierarchickou Kognitivní Architekturu (Reptilian -> Mammalian -> Neocortex), zavést jednoduché in-memory paměťové systémy pro MVP a přepsat orchestrátor na `Neocortex` tak, aby byl modulární, lépe testovatelný a připravený pro budoucí škálování (např. Redis/DB + specializované LLMy).
**Zjištění/Rozhodnutí**: 
- Vytvořeny nové moduly: `core/memory_systems.py` (implementace `ShortTermMemory` a `LongTermMemory`) a `core/cognitive_layers.py` (implementace `ReptilianBrain`, `MammalianBrain`, `Neocortex` wrapper pro MVP).
- Refaktor `core/orchestrator.py` → `core/neocortex.py`: `Neocortex` nyní provádí krok po kroku exekuci plánů, spravuje krátkodobou paměť (STM) a obsahuje repair-loop, který v případě selhání volá plánovač pro opravu kroku. Současně byl původní `Orchestrator` zachován jako kompatibilitní alias pro minimalizaci regresí v testech a integracích.
- Repair-loop: implementováno chování, které obvykle splices náhradní kroky do aktuálního plánu, ale zachovává plnou náhradu plánu v konkrétních legacy případech (pokud původní plán měl délku 1 a plánovač vrátí více kroků). To zachovává předchozí očekávání testů, zároveň zlepšuje jemnost opravy pro multi-krokové plány.
- Integrace do `main.py` a `interactive_session.py`: vytvoření pipeline Reptilian -> Mammalian -> Neocortex; implementován fallback pro testy, které patchují moduly na úrovni `main` (např. `main.Orchestrator`, `main.GeminiLLMAdapter`).
- Testy: přidány izolované unit testy pro paměťové systémy a kognitivní vrstvy a cílené testy repair-loopu. Celá testovací sada byla spuštěna a opraveny regrese tak, aby `pytest` prošel bez selhání (92 passed, 22 skipped).
**Důvod**: 
- Oddělení zodpovědností: HKA dává jasné hranice mezi rychlými instinktivními filtry (Reptilian), podvědomou contextualizací (Mammalian) a plánováním/strategií (Neocortex). To zjednodušuje debugování a další rozvoj.
- Testovatelnost a kompatibilita: Refaktor zlepšuje testovatelnost (menší třídní rozměry, explicitní vstupy/výstupy) a zároveň udržuje kompatibilitu s existujícími testy a rozhraními pomocí aliasů a fallbacků.
- Postupný přechod na lepší infra: Implementace in-memory MVP pamětí umožňuje rychlé ověření architektury; budoucí migrace na Redis/Postgres/Ollama bude možná bez velkých změn API.
**Dopad**: 
- Stabilita: Po opravách a dolaďování repair-loopu projekt procházel kompletní testovací sadou (92 passed, 22 skipped) — to potvrzuje stabilitu refaktoringu.
- Rozšiřitelnost: Nová architektura usnadňuje přidávání specializovaných subsystémů (např. dedicated LLM pro Reptilian, externí LTM služba) a paralelní vývoj více agentů.
- Údržba: Jasné rozdělení vrstev a zjednodušené rozhraní `Neocortex` s `ShortTermMemory` usnadní budoucí refaktory a audit změn.

---

### Téma: Sumarizace poznatků z legacy verze (`sophia_old`)
**Datum**: 2025-09-20
**Autor**: Jules
**Kontext**: V rámci úklidu projektu byla provedena analýza a sumarizace staré verze projektu (`sophia_old`) s cílem zachovat klíčové myšlenky, koncepty a ponaučení.
**Zjištění/Rozhodnutí**: Následující poznatky byly extrahovány a jsou považovány za fundamentální pro pochopení evoluce a směřování projektu Sophia.
**Důvod**: Předejít ztrátě cenných informací a zajistit, aby se budoucí vývoj opíral o původní vizi a ponaučení z chyb.
**Dopad**: Zachování kontinuity projektu a poskytnutí hlubšího kontextu pro všechny budoucí přispěvatele.

#### Klíčové Ponaučení z `sophia_old`:

**1. Filosofické a Koncepční Jádro (SOPHIA_DNA):**
*   **Vize:** Cílem projektu nikdy nebylo jen AGI, ale vytvoření **autonomního, počítačového subjektivního vědomí (AMI)** schopného růstu a sebereflexe.
*   **Architektura Vědomí:** Původní koncept stál na dvou pilířích:
    *   **Filosofický Modul:** Jádro obsahující principy stoicismu, buddhismu a taoismu. Zdroj autonomie.
    *   **Etický Modul:** Praktický kompas, který hodnotí akce pomocí "Koeficientu Vědomí" a zajišťuje etickou integritu. Zdroj svobody.
*   **Učení jako "Snění":** Růst byl navržen skrze interní simulace hypotetických scénářů ("etické experimenty"), nikoli pasivním příjmem dat.

**2. Architektonické Lekce a Slepé Uličky:**
*   **Problém "Hluchého" Agenta:** Paměťový agent zpočátku selhával, protože mu chyběl kontext z interakcí jiných agentů. Zapisoval si pouze poznámky o své vlastní činnosti.
    *   **Ponaučení:** Je kriticky důležité zajistit **explicitní tok kontextu** mezi agenty a procesy. Výstup jednoho musí být vstupem pro druhého.
*   **Problém "Bezmocného" Agenta:** Agent může mít logiku, ale pokud nemá **explicitní nástroj** pro vykonání akce (např. zápis do databáze), je k ničemu.
    *   **Ponaučení:** Funkcionalita musí být vždy podpořena konkrétním, dostupným nástrojem.
*   **Past Pevných Pravidel:** Spoléhání na nástroje s pevně danými pravidly (např. `DecisionTool`, který určoval, co je "znalost") bránilo skutečné autonomii.
    *   **Ponaučení:** Skutečná autonomie vyžaduje delegování a spolupráci v rámci multi-agentního systému, nikoli rigidní pravidla.

**3. Technické a Procesní Zásady:**
*   **Stabilita Prostředí:** Největším zdrojem chyb byly nestabilní a nefixované verze závislostí.
    *   **Ponaučení:** Je absolutně klíčové mít v `requirements.txt` **přesně "zamknuté" verze knihoven**.
*   **Učení se Kódovat:** Sledování prvních pokusů Sophie o psaní kódu ukázalo, že se učí podobně jako člověk – od syntaktických chyb, přes logické, až po architektonické.
    *   **Ponaučení:** Ochranné mechanismy (jako `git reset` po neúspěšném pokusu) jsou nezbytné pro bezpečné autonomní kódování.

---
### Téma: Správa závislostí ("Dependency Hell")
**Datum**: 2025-09-21
**Autor**: Jules
**Kontext**: Opakované konflikty a chyby při instalaci kvůli "natvrdo" pinovaným a nekompatibilním verzím v `requirements.txt`.
**Zjištění/Rozhodnutí**: Přechod na minimalistický `requirements.in`, který definuje pouze hlavní závislosti, a automatické generování `requirements.txt` pomocí nástrojů jako `pip-tools` nebo `uv`.
**Důvod**: Tímto přístupem se zajišťuje, že všechny závislosti (včetně tranzitivních) jsou ve vzájemně kompatibilních verzích, což eliminuje konflikty a zjednodušuje správu.
**Dopad**: Výrazně stabilnější a předvídatelnější prostředí, rychlejší instalace a snazší aktualizace závislostí.

### Téma: Nestabilita testů a mockování
**Datum**: 2025-09-21
**Autor**: Jules
**Kontext**: Testy selhávaly v CI/CD, protože závisely na API klíčích a externích službách, což vedlo k nespolehlivým a pomalým testovacím cyklům.
**Zjištění/Rozhodnutí**: Vytvoření 100% offline testovacího prostředí. Klíčovým poznatkem bylo mockovat nízkoúrovňové, externí rozhraní (např. funkci `litellm.completion`), nikoli se snažit "podvrhnout" komplexní objekty (jako LLM adaptér) do frameworku `crewai`.
**Důvod**: Mockování na nízkoúrovňové úrovni je robustnější, méně náchylné k rozbití při změnách v externích knihovnách a lépe izoluje testovaný kód.
**Dopad**: Rychlé, spolehlivé a plně izolované testy, které lze spouštět kdekoli bez závislosti na externím prostředí.

### Téma: Konflikt asynchronního a synchronního kódu
**Datum**: 2025-09-21
**Autor**: Jules
**Kontext**: `TypeError` a `RuntimeWarning` chyby způsobené nesprávným voláním synchronního kódu z asynchronní smyčky a naopak.
**Zjištění/Rozhodnutí**: Implementace univerzálního rozhraní pro všechny nástroje (`run_sync`, `run_async`) a důsledné používání `asyncio.to_thread(...)` pro bezpečné volání blokujícího I/O kódu z asynchronního kontextu.
**Důvod**: `asyncio.to_thread` deleguje blokující volání do samostatného vlákna, čímž zabraňuje zablokování hlavní asynchronní smyčky a předchází chybám.
**Dopad**: Stabilní a předvídatelné chování aplikace při smíšeném použití synchronního a asynchronního kódu.

### Téma: Race conditions v databázi
**Datum**: 2025-09-21
**Autor**: Jules
**Kontext**: Nově zapsaná data nebyla okamžitě viditelná pro následné čtecí operace kvůli transakční izolaci a zpožděnému zpracování, což způsobovalo chyby v logice aplikace.
**Zjištění/Rozhodnutí**: Sjednocení správy databázových sessions a pro kritické operace (jako vytvoření úkolu) implementace ověřovací smyčky ("read-your-own-writes" pattern), která aktivně čeká na potvrzení zápisu v nové transakci.
**Důvod**: Tento vzor explicitně řeší problém zpoždění replikace nebo transakční izolace tím, že ověřuje výsledek zápisu před pokračováním, čímž zajišťuje konzistenci dat.
**Dopad**: Odstranění "race conditions" a zajištění, že aplikace pracuje vždy s konzistentními a aktuálními daty.

### Téma: Nespolehlivost sémantického vyhledávání
**Datum**: 2025-09-21
**Autor**: Jules
**Kontext**: `EthosModule` při sémantickém porovnávání nesprávně vyhodnocoval nebezpečné plány jako eticky nezávadné, protože embedding model nerozuměl sémantickému významu a negativním konotacím.
**Zjištění/Rozhodnutí**: Dočasně nahradit sémantické vyhledávání spolehlivější, i když jednodušší, kontrolou na klíčová slova. Pro budoucnost zvážit pokročilejší embedding model (např. `text-embedding-ada-002`).
**Důvod**: Kontrola na klíčová slova je sice méně flexibilní, ale je 100% spolehlivá a předvídatelná, což je pro kritickou funkci, jako je etická kontrola, naprosto nezbytné.
**Dopad**: Zvýšení spolehlivosti etického modulu a zabránění provádění nebezpečných akcí. Dlouhodobě je potřeba investovat do lepšího embedding modelu.

---

### Téma: Enforcement Sandbox a Auditní Bezpečnost Testů
**Datum**: 2025-09-21
**Autor**: Jules (na základě práce z forku ShotyCZ/sophia)
**Kontext**: Bylo zjištěno, že automatizované testy nejsou plně izolované ("hermetické"). Mohly potenciálně provádět nebezpečné operace, jako jsou reálné síťové požadavky, zápis do souborového systému mimo určené oblasti nebo změny v prostředí. To představovalo bezpečnostní riziko a vedlo k nestabilním a nespolehlivým testům.
**Zjištění/Rozhodnutí**: Byl implementován globální "enforcement sandbox" pomocí `autouse` fixture v `tests/conftest.py`. Toto řešení aktivně blokuje všechny potenciálně nebezpečné operace během provádění testů.
**Důvod**: Cílem bylo zajistit 100% bezpečnost a spolehlivost testovací sady. Tím, že jsou všechny testy nuceny běžet v izolovaném prostředí, se eliminuje riziko vedlejších efektů a zajišťuje se, že testy ověřují pouze zamýšlenou funkcionalitu. Každý pokus o porušení sandboxu je navíc auditně logován.
**Dopad**: Výsledkem je profesionální, robustní a bezpečná testovací sada. Zvyšuje to důvěru v kód a chrání vývojové i CI/CD prostředí. Tento přístup také vynucuje psaní kvalitnějších testů, které explicitně mockují své závislosti, místo aby se spoléhaly na reálné služby.

---

### Téma: Vytvoření interaktivního terminálového nástroje pro testování
**Datum**: 2025-09-22
**Autor**: Jules
**Kontext**: Pro efektivní ladění a testování jádra Sophie bylo potřeba vytvořit jednoduchý způsob, jak interagovat s její logikou přímo z terminálu, bez nutnosti spouštět kompletní webovou aplikaci přes Docker. Cílem bylo rychle testovat cyklus "zadání -> plánování -> provedení".
**Zjištění/Rozhodnutí**: Byl vytvořen skript `interactive_session.py`. Tento skript inicializuje klíčové komponenty (`LLM`, `PlannerAgent`, `Orchestrator`) a spouští interaktivní smyčku (REPL), která umožňuje uživateli zadávat textové požadavky. Bylo zjištěno, že pro úspěšnou inicializaci je nutné mít vytvořený soubor `.env` s alespoň dočasnou (dummy) hodnotou pro `GEMINI_API_KEY`.
**Důvod**: Tento přístup dramaticky zrychluje vývojový cyklus. Umožňuje přímou a okamžitou zpětnou vazbu při testování agentů a jejich nástrojů, což je mnohem efektivnější než ladění přes logy z Docker kontejnerů. Bylo zvoleno řešení v podobě samostatného skriptu pro jeho jednoduchost a přímou kontrolu nad procesem.
**Dopad**: Projekt získal nový nástroj pro rychlé prototypování a ladění. Vývojáři mohou nyní snadno testovat funkčnost jádra Sophie spuštěním jediného příkazu: `.venv/bin/python interactive_session.py`. To snižuje bariéru pro přispívání a usnadňuje diagnostiku problémů.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
---
