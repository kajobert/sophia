# Akční plán optimalizace a zlepšení (2025-09-15)

Tento plán rozpracovává jednotlivé návrhy na konkrétní kroky, které zvýší efektivitu, rychlost a udržitelnost projektu Sophia. Každý bod obsahuje jasný popis, cíl a doporučený postup.

## 1. Backend: výkon, škálovatelnost, bezpečnost

### 1.1 Přechod na asynchronní framework (FastAPI)
- [x] **Cíl:** Získat vyšší výkon, async endpointy, automatickou OpenAPI dokumentaci.
- [x] **Postup:**
    - Backend přepsán na FastAPI (asynchronní, OpenAPI, Authlib, session, endpoints)
    - Všechny endpointy refaktorovány na async funkce
    - Ověřena kompatibilita s frontendem a testy

### 1.2 Centralizace konfigurace
- [x] **Cíl:** Jednoduchá správa prostředí, bezpečnost, přehlednost.
- [x] **Postup:**
    - Vytvořen modul `core/config.py` pro všechny proměnné prostředí, cesty, admin emaily, test mode
    - Všechny části backendu načítají konfiguraci pouze z tohoto modulu

### 1.3 Oddělení business logiky od endpointů
- [x] **Cíl:** Lepší čitelnost, testovatelnost, rozšiřitelnost.
- [x] **Postup:**
    - Každý endpoint volá pouze tenkou vrstvu, logika je v samostatných modulech/službách (`services/`)
    - Všechny služby odděleny dle domény (uživatelé, role, chat, tokeny, audit)

### 1.4 JWT místo session cookies (volitelné)
- **Cíl:** Škálovatelnost, možnost více backend instancí bez sdílené session.
- **Postup:**
    - Implementovat JWT autentizaci (např. pomocí PyJWT)
    - Zajistit kompatibilitu s frontendem

### 1.5 Bezpečnostní vylepšení
- [x] **Cíl:** Ochrana proti CSRF, XSS, session hijackingu.
- [x] **Postup:**
    - Nastaveny secure cookies, SameSite, session management
    - Implementováno RBAC (role-based access control)
    - Přidány refresh tokeny (JWT) pro bezpečné prodloužení session
    - Implementováno auditní logování všech bezpečnostních akcí
    - Pravidelně auditovat závislosti (Bandit, Snyk)

## 2. Testování a CI/CD

### 2.1 Mockování OAuth2 pro testy
- [x] **Cíl:** Plně automatizované testy bez nutnosti interakce s Googlem.
- [x] **Postup:**
    - Test mode umožňuje simulovat login bez Google OAuth2
    - Pokryty scénáře úspěchu, selhání, expirovaný token

### 2.2 Pokrytí testy a coverage
- [x] **Cíl:** Zajistit spolehlivost a odhalit chyby v edge-case scénářích.
- [x] **Postup:**
    - Všechny nové funkce (RBAC, refresh, audit) pokryty testy v `tests/web_api/test_api_basic.py`
    - Pravidelně doplňovat testy pro nové i existující funkce

### 2.3 CI/CD pipeline
- **Cíl:** Automatizace build, test, lint, nasazení.
- **Postup:**
    - Nastavit GitHub Actions workflow pro lint, testy, build, deployment
    - Přidat badge do README

## 3. Frontend: UX, výkon, testy

### 3.1 State management
- **Cíl:** Jednotná správa uživatele, session, notifikací.
- **Postup:**
    - Zavést Redux, Zustand nebo Context API
    - Refaktorovat komponenty na využití centralizovaného stavu

### 3.2 Lazy loading a optimalizace bundle
- **Cíl:** Rychlejší načítání, menší bundle.
- **Postup:**
    - Rozdělit velké komponenty, použít React.lazy/Suspense
    - Optimalizovat build (tree-shaking, code splitting)

### 3.3 E2E testy
- **Cíl:** Automatizované testy uživatelských scénářů.
- **Postup:**
    - Zavést Cypress nebo Playwright
    - Pokrýt hlavní scénáře (login, chat, upload, odhlášení)

## 4. Dokumentace a Dev Experience

### 4.1 OpenAPI/Swagger dokumentace
- [x] **Cíl:** Automaticky generovaná a aktuální API dokumentace.
- [x] **Postup:**
    - FastAPI generuje OpenAPI dokumentaci automaticky na /docs

### 4.2 Onboarding a přehlednost
- [x] **Cíl:** Rychlý start pro nové vývojáře, přehledná architektura.
- [x] **Postup:**
    - README.md a ARCHITECTURE.md doplněny o aktuální architekturu a quickstart
    - Přidán příklad proměnných prostředí do INSTALL.md

## 5. Výkon a škálovatelnost

### 5.1 Asynchronní background jobs
- [ ] **Cíl:** Oddělit náročné úlohy od request/response cyklu.
- [ ] **Postup:**
    - (Plánováno, zatím neimplementováno)

### 5.2 Cache
- **Cíl:** Zrychlit často volané endpointy.
- **Postup:**
    - Zavést Redis/memcached pro cache uživatelských dat, výsledků dotazů

### 5.3 Optimalizace přístupu do paměti/databáze
- **Cíl:** Snížit latenci, zvýšit propustnost.
- **Postup:**
    - Profilovat a optimalizovat dotazy, zavést batch operace, indexy

## 6. Bezpečnost a audit

### 6.1 Auditní logy a monitoring
- **Cíl:** Sledovat a analyzovat klíčové akce a incidenty.
- **Postup:**
    - Logovat přihlášení, odhlášení, změny dat, chyby, podezřelé akce
    - Nastavit alerty na kritické události

### 6.2 Rate limiting
- **Cíl:** Ochrana proti zneužití API.
- **Postup:**
    - Zavést rate limiting (např. Flask-Limiter, FastAPI-limiter)

### 6.3 Bezpečnostní skeny
- **Cíl:** Pravidelně odhalovat zranitelnosti v závislostech.
- **Postup:**
    - Používat Bandit, Snyk, Dependabot

## 7. Modularita a rozšiřitelnost

### 7.1 Plugin architektura pro agenty
- **Cíl:** Umožnit snadné přidávání nových agentů a nástrojů.
- **Postup:**
    - Navrhnout rozhraní pro pluginy, oddělit jádro a rozšíření

### 7.2 Oddělení sandboxu a produkce
- **Cíl:** Bezpečné experimenty bez vlivu na produkci.
- **Postup:**
    - Sandbox držet odděleně, jasná pravidla pro migraci změn

# Projekt Sophia V4: Roadmapa k Autonomnímu Tvůrci

Tento dokument slouží jako hlavní plán a TODO list pro vývoj AGI Sophia V4. Cílem této etapy je přeměnit Sophii z myslitele na autonomního tvůrce, který dokáže samostatně psát, testovat a vylepšovat kód v bezpečném prostředí.

## CÍLOVÝ STAV: Sophia V4 - Autonomní Tvůrce

Cílem je vytvořit systém, který:
-   Disponuje robustní infrastrukturou (PostgreSQL, proaktivní monitoring).
-   Využívá pokročilé open-source nástroje pro paměť a etiku.
-   Pro exekutivní úkoly používá disciplinovaný tým agentů (CrewAI).
-   Pro kreativní a sebereflexivní procesy využívá flexibilní tým agentů (AutoGen).
-   Dokáže v sandboxu samostatně naplánovat, napsat a otestovat funkční kód.

---

## Roadmapa Implementace V4

### Fáze 9: Evoluce Infrastruktury


**Cíl:** Připravit robustní, škálovatelné a bezpečné prostředí pro autonomní operace.

- [x] **9.1. Upgrade Databáze:**
    -   Nahradit stávající řešení s SQLite za client-server databázi PostgreSQL.
    -   Upravit `memory/episodic_memory.py` a `web/api.py` pro práci s novou databází.
    -   Aktualizovat `requirements.txt` o `psycopg2-binary` nebo podobný driver.
    -   Aktualizovat `INSTALL.md` a `setup.sh` s instrukcemi pro spuštění PostgreSQL (např. pomocí Dockeru).

- [x] **9.2. Inteligentní Guardian:**
    -   Integrovat knihovnu `psutil` do `guardian.py`.
    -   Rozšířit monitorovací smyčku o kontrolu systémových prostředků (využití CPU a RAM).
    -   Implementovat logiku, která v případě překročení prahových hodnot (např. 90% RAM) provede "měkký" restart nebo pošle varování.
    -   **Modularizace guardian.py:** Pokročilé kontroly (integrita, logy, síť) přesunuty do samostatného modulu `sophia_monitor.py`.
    -   **Testování:** Vytvořeny a upraveny testy pro guardian i sophia_monitor (pytest, plné pokrytí základních scénářů).
    -   **Dokumentace:** Přidán seznam plánovaných kontrol do `sophia_monitor.py` a aktualizován WORKLOG.

- [x] **9.3. Vytvoření Sandboxu:**
    -   Vytvořit a zabezpečit adresář `/sandbox`.
    -   Zajistit, aby kód spuštěný v sandboxu neměl přístup k souborům mimo tento adresář.


### Fáze 10: Vybavení Dílny

**Cíl:** Vytvořit a integrovat pokročilé nástroje, které agentům umožní efektivně pracovat.

- [x] **10.1. Implementace Pokročilé Paměti:**
    -   Prozkoumat a integrovat externí paměťovou knihovnu (např. `GibsonAI/memori`).
    -   Nahradit naši stávající jednoduchou logiku pro "váhu" a "blednutí" za robustnější řešení z této knihovny.
    -   Refaktorovat MemoryReaderTool a všechny paměťové nástroje na univerzální async/sync rozhraní (hotovo, viz WORKLOG.md 2025-09-14 22:30).

- [x] **10.2. Nástroje pro Tvorbu:**
    -   Vytvořit `tools/file_system.py` s nástroji pro čtení, zápis, a výpis souborů v `/sandbox` (hotovo, univerzální async/sync rozhraní).
    -   Vytvořit `tools/code_executor.py` s nástroji pro spouštění Python skriptů a `unittest` testů v `/sandbox` a zachytávání jejich výstupu a chyb (hotovo, univerzální async/sync rozhraní).
    -   Všechny nástroje nyní podporují bezpečné použití v CrewAI (sync) i AutoGen (async) workflow.

### Fáze 11: Zrození Týmu Tvůrců

**Cíl:** Vylepšit etické jádro a implementovat agenty schopné psát a testovat kód.

- [x] **11.1. Konstituční AI:**
    -   Prozkoumat a integrovat knihovnu `LangGraph`.
    -   Přepracovat `core/ethos_module.py`, aby používal cyklický proces (kritika -> revize) inspirovaný Konstituční AI, místo jednoduchého porovnání.

- [x] **11.2. Oživení Agentů (CrewAI):**
    -   Plně implementovat `agents/engineer_agent.py` a vybavit ho nástroji pro práci se soubory a spouštění kódu.
    -   Plně implementovat `agents/tester_agent.py` a vybavit ho stejnými nástroji.

### Fáze 12: Probuzení Kreativity

**Cíl:** Uzavřít smyčku autonomní tvorby a rozšířit schopnosti o kreativní procesy.

- [x] **12.1. Tým Snů (AutoGen):**
    -   Prozkoumat a integrovat framework `AutoGen`.
    -   Vytvořit specializovaný tým agentů (`Philosopher`, `Architect`) v `AutoGen`, který bude aktivován během "spánkové" fáze pro generování nových nápadů a strategií.

- [x] **12.2. Uzavření Smyčky Tvorby:**
    -   Upravit `core/consciousness_loop.py` tak, aby dokázal orchestrovat celý řetězec: `Planner` -> `Engineer` -> `Tester`.
    -   Implementovat logiku pro zpracování zpětné vazby (např. když testy selžou, úkol se vrátí Inženýrovi s chybovou hláškou).

---

### Fáze 13: Integrace Aider IDE Agenta

**Cíl:** Využít Aider IDE jako autonomní evoluční motor – agent, který umožní Sophii samostatně navrhovat, upravovat a refaktorovat vlastní kód v sandboxu, a tím realizovat skutečnou autonomní evoluci schopností.

- [x] **13.1. Analýza a příprava integrace:**
    -   Prozkoumat možnosti Aider IDE (https://github.com/paul-gauthier/aider) a jeho CLI/API.
    -   Navrhnout Aider IDE jako samostatného autonomního agenta s právem měnit kód Sophie v sandboxu.
- [x] **13.2. Implementace AiderAgent:**
    -   Vytvořit wrapper třídu `AiderAgent` v `agents/aider_agent.py` pro komunikaci s Aider IDE přes CLI.
    -   Definovat protokol pro předávání úkolů (např. JSON přes stdin/stdout nebo REST endpoint).
    -   Omezit všechny operace na `/sandbox` a validovat výstup před commitem.
    -   Zajistit, že všechny změny budou auditovatelné (git log, review) a podléhají etické kontrole (Ethos module, případně schválení jiným agentem).
- [x] **13.3. Evoluční workflow:**
    -   Umožnit Aider agentovi samostatně navrhovat a realizovat změny kódu na základě cílů nebo vlastního rozhodnutí v rámci evoluční smyčky.
    -   Ostatní agenti (Planner, Philosopher, Architect) navrhují cíle, hodnotí změny a poskytují zpětnou vazbu, ale Aider agent provádí úpravy.
    -   Všechny změny musí být bezpečné, auditované a revertovatelné.
    -   Odstranit zbytečnou delegaci a složitou mezivrstvu – Aider agent je hlavní motor evoluce.
    -   Pravidelně revidovat, zda některé mechanismy nejsou redundantní nebo překonané a roadmapu dále zjednodušovat.

### Fáze 14: Robustní LLM integrace (GeminiLLMAdapter)

**Cíl:** Zajistit robustní, snadno vyměnitelnou a testovatelnou integraci LLM pro všechny agenty.

- [x] **14.1. Návrh a implementace GeminiLLMAdapter:**
    -   Navrhnout a implementovat vlastní adapter pro Google Gemini API (`core/gemini_llm_adapter.py`).
    -   Zajistit kompatibilitu s CrewAI a orchestrace agentů (předávání `llm=llm`).
    -   Připravit možnost snadného přepnutí na LangChain wrapper v budoucnu.
    -   Implementovat sledování spotřeby tokenů a základní testy.
    -   Aktualizovat dokumentaci (`README.md`, `INSTALL.md`, `ARCHITECTURE.md`, `CONCEPTS.md`).
    -   Ověřit, že všichni agenti používají nový adapter a vše je plně funkční.
    -   Přidat závislost `google-generativeai` do requirements.txt.
    -   Otestovat inicializaci a základní workflow agentů s novým adapterem.
    -   Zapsat změny do WORKLOG.md a roadmapy.

---

### Fáze 15: Webové rozhraní a testování (React UI)

**Cíl:** Implementovat a zdokumentovat frontendovou SPA aplikaci, ověřit její funkčnost a propojení s backendem.

- [x] **15.1. Struktura a základní UI:**
    -   Vytvořit adresář `web/ui/`, připravit strukturu pro React SPA.
    -   Implementovat hlavní komponenty (Chat, Login, Upload, Files, Profile, Notifications, Settings, Helpdesk, Language, RoleManager).
    -   Všechny funkce mají tlačítka v hlavním menu (zatím placeholdery).
    -   Zapsat do WORKLOG.md.
- [x] **15.2. Propojení s backendem a testování:**
    -   Ověřit komunikaci s backendem (login, chat endpoint).
    -   Implementovat integrační testy (Jest, Testing Library).
    -   Zapsat do WORKLOG.md.
- [x] **15.3. Dokumentace:**
    -   Doplnit README.md, INSTALL.md, ARCHITECTURE.md o sekci pro frontend.
    -   Zapsat změny do WORKLOG.md a roadmapy.