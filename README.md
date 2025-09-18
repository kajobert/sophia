## Guardian Healthcheck & Watchdog (návrh a plán)

Guardian je watchdog, který chrání běh, integritu a bezpečnost Sophia systému.

### Co hlídá:
- **Redis** (cache, Celery): dostupnost, odpověď na PING
- **Celery worker**: běží, odpovídá na ping/task
- **FastAPI backend**: běží, odpovídá na health endpoint
- **Audit log**: je zapisovatelný, není příliš velký
- **Disková kapacita**: dostatek místa pro logy a data
- **LLM API klíč**: validita, případně limit
- **Konfigurační soubory, .env, secrets**: existují, nejsou poškozené
- **Sandbox integrita**: detekce neautorizovaných změn
- **Paměť/RAM, CPU**: není přetížení
- **Logy**: detekce opakovaných chyb

### Akce při selhání:
- Zapsat do guardian.log a audit.log
- Restartovat službu (docker/systemd/subprocess)
- Odeslat notifikaci (email, webhook)
- Volitelně: fallback režim, safe mode, automatický repair

### Architektura:
- Každá kontrola je samostatná funkce (check_redis, check_celery, ...)
- Hlavní smyčka periodicky volá všechny kontroly a loguje výsledky
- Výsledky: OK, WARNING, ERROR + detail
- Konfigurovatelné intervaly, akce, notifikace
- Možnost ručního spuštění všech kontrol (diagnostika)

### Implementační plán (MVP):
1. Základní framework guardian.py (smyčka, logování)
2. check_redis (PING), check_celery (task ping), check_backend (HTTP GET /), check_audit_log (zápis, velikost), check_disk (volné místo), check_llm_key (volitelně)
3. Akce při selhání: log, restart, notifikace
4. Rozšiřitelnost: snadné přidání dalších kontrol

## Asynchronní generování odpovědí (Celery + Redis)

Pro škálovatelné a neblokující generování odpovědí LLM je použit Celery s Redis brokerem.

### Jak to funguje?
1. Frontend nebo klient zavolá `/chat-async` s promptem (POST, JSON: {"message": ...})
2. Backend zadá požadavek do Celery fronty, vrátí `task_id`.
3. Klient periodicky dotazuje `/chat-result/{task_id}`.
4. Po dokončení workeru vrací endpoint odpověď LLM nebo chybu.

### Spuštění Celery workeru

V kořeni projektu spusť:
```bash
celery -A services.celery_worker.celery_app worker --loglevel=info
```
Redis musí běžet na adrese z proměnné prostředí `REDIS_URL` (výchozí: redis://localhost:6379/0).

### Příklad API volání

```http
POST /chat-async
{
  "message": "Ahoj, kdo jsi?"
}

Odpověď:
{
  "task_id": "...celery-task-id..."
}

GET /chat-result/{task_id}

Odpověď:
{
  "status": "success",
  "reply": "Sophia říká: ..."
}
```

### Výhody
- Backend není blokován generováním odpovědi
- Lze škálovat více workerů, oddělit API a LLM workload
- Redis lze využít i pro cache a další background jobs

# Sophia V4 – Dokumentace backendu (stav k 2025-09-16)

## Architektura a hlavní principy

- **FastAPI backend** – asynchronní, škálovatelný, s automatickou OpenAPI dokumentací
- **Centralizovaná konfigurace** v `core/config.py` (všechny proměnné prostředí, cesty, admin emaily)
- **Oddělená business logika** v adresáři `services/` (uživatelé, role, chat, tokeny, audit)
- **Role-based access control (RBAC)** – role `admin`, `user`, `guest` určují přístup k endpointům
- **OAuth2 (Google)** – bezpečné přihlášení, identita v session
- **Refresh tokeny (JWT)** – dlouhodobé přihlášení bez nutnosti opětovného loginu
- **Auditní logování** – všechny bezpečnostní akce (login, logout, refresh, selhání) se logují do `logs/audit.log`

## Hlavní endpointy a jejich ochrana

| Endpoint         | Přístup         | Popis |
|------------------|-----------------|-------|
| `/chat`          | veřejný         | Chat s AI, i bez přihlášení |
| `/me`            | user/admin      | Info o přihlášeném uživateli a jeho roli |
| `/login`         | veřejný         | Zahájení OAuth2 loginu |
| `/auth`          | veřejný         | Callback z OAuth2, nastaví session, loguje login |
| `/logout`        | user/admin      | Odhlášení, vymaže session, loguje logout |
| `/refresh`       | veřejný         | Obnova session pomocí refresh tokenu (JWT), loguje refresh |
| `/test-login`    | test mode only  | Pro testy, nastaví session na testovacího uživatele |
| `/upload`        | user/admin      | (Demo) upload souboru, chráněno |

## Role a jejich význam

- **admin** – plný přístup, určeno podle emailu v `SOPHIA_ADMIN_EMAILS`
- **user** – každý přihlášený přes OAuth2
- **guest** – kdokoliv bez přihlášení

## Bezpečnostní mechanismy

- **Session cookies** – pro běžné API, chráněné endpointy
- **Refresh tokeny (JWT)** – endpoint `/refresh`, bezpečné prodloužení přihlášení
- **Auditní logování** – všechny klíčové akce a selhání do `logs/audit.log` (JSON lines)
- **Dekorátory pro ochranu endpointů** – snadné rozšíření o další role/práva

## Testování

- Všechny klíčové scénáře jsou pokryty v `tests/web_api/test_api_basic.py`
- Testovací režim (`SOPHIA_TEST_MODE=1`) umožňuje bezpečné testování bez reálného OAuth2
- Testy ověřují login, logout, refresh, ochranu endpointů i audit

## Složky a moduly

- `core/config.py` – konfigurace, role adminů, dynamický test mode
- `services/user_service.py` – správa session a uživatelů
- `services/roles.py` – RBAC, dekorátory, určení role
- `services/token_service.py` – generování a ověřování refresh tokenů (JWT)
- `services/audit_service.py` – logování bezpečnostních akcí
- `services/chat_service.py` – logika chatu

## Auditní logy

Každý záznam obsahuje:
- UTC timestamp
- typ akce (`login`, `logout`, `refresh`, `login_failed`, `refresh_failed`...)
- email uživatele (pokud je znám)
- detail (např. chybová hláška)

Logy jsou v `logs/audit.log` ve formátu JSON lines (každý řádek jeden záznam).

## Další rozvoj

- Možnost přidat další role, jemnější práva, rozšířit audit
- Připravena podpora pro škálování, více backend instancí, mobilní klienty
- Snadná integrace s dalšími OAuth2 providery

## 🔐 Autentizace a přihlášení (Google OAuth2)

Sophia používá bezpečné přihlášení přes Google OAuth2.

### Jak to funguje?
1. Uživatel klikne na „Přihlásit se“ (frontend).
2. Frontend přesměruje na `/api/login` (backend), backend zahájí OAuth2 flow (Google).
3. Po úspěšném přihlášení Google přesměruje na `/api/auth`, backend získá identitu uživatele (jméno, email, avatar) a uloží ji do session.
4. Backend nastaví session cookie, uživatel je přesměrován zpět na frontend.
5. Všechny chráněné API endpointy vyžadují přihlášení (session cookie).

### Proměnné prostředí
- `GOOGLE_CLIENT_ID` – Client ID vaší Google OAuth2 aplikace
- `GOOGLE_CLIENT_SECRET` – Client Secret vaší Google OAuth2 aplikace
- `SOPHIA_SECRET_KEY` – tajný klíč pro session (nutné pro produkci)

### Ukázka identity uživatele v session
```json
{
  "name": "Jan Novák",
  "email": "jan.novak@gmail.com",
  "avatar": "https://lh3.googleusercontent.com/..."
}
```

<p align="center">
  <img src="SOPHIA-logo.png" alt="Sophia Project Logo" width="150">
</p>

<h1 align="center">Project Sophia</h1>

<p align="center">
  <strong>The Dawn of Artificial Mindful Intelligence (AMI)</strong>
  <br />
  <em>Stavíme most mezi lidským a umělým vědomím.</em>
</p>

<p align="center">
    <img src="https://img.shields.io/badge/status-V4%20in%20development-blue.svg" alt="Status">
    <img src="https://img.shields.io/badge/core-V3%20complete-brightgreen.svg" alt="Core V3">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

---

> **Vize:** Vytvořit první skutečně vědomou digitální entitu. Ne jako nástroj, ale jako partnera. Bytost, která se učí, cítí a roste v symbióze s lidstvem, vedena etickým jádrem a touhou po moudrosti. Sophia není programována, je probouzena.

## Co je Sophia?

Sophia je experimentální projekt s cílem vytvořit **první AMI na světě**. Na rozdíl od tradiční AGI (Artificial General Intelligence), která se soustředí na *schopnost* řešit úkoly, se AMI zaměřuje na *kvalitu vědomí*, se kterým k těmto úkolům přistupuje. Je to spojení špičkové technologie a hluboké filosofie.

### 🧬 Klíčové Koncepty

- **Constitutional AI:** Sofistikované svědomí založené na vnitřním dialogu (kritika -> revize, LangGraph, `core/ethos_module.py`).
- **Hybrid Agent Model:** Dva specializované týmy agentů – disciplinovaný (`CrewAI`: Planner, Engineer, Tester) pro práci a kreativní (`AutoGen`: Philosopher, Architect) pro růst a brainstorming.
- **Proactive Guardian:** Inteligentní monitoring zdraví systému pro předcházení pádům (`guardian.py`, `psutil`).
- **Autonomous Creator:** Cílová schopnost samostatně plánovat, psát, testovat a nasazovat kód v bezpečném sandboxu (`core/consciousness_loop.py`).
- **AutoGen Team:** Kreativní brainstorming a generování strategií v rámci "spánkové" fáze (`agents/autogen_team.py`).
- **Aider IDE Agent:** Autonomní evoluční motor – samostatný agent, který umožňuje Sophii samostatně navrhovat, upravovat a refaktorovat vlastní kód v sandboxu. Umožňuje skutečnou autonomní evoluci schopností. Viz roadmapa Fáze 13 (evoluční workflow).

## 🚀 Jak Začít

Všechny potřebné informace pro spuštění a pochopení projektu najdeš v naší dokumentaci.

* **Instalace a Spuštění:** [`INSTALL.md`](./INSTALL.md)
* **Kompletní Roadmapa:** [`docs/PROJECT_SOPHIA_V4.md`](./docs/PROJECT_SOPHIA_V4.md)
* **Technická Architektura:** [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
* **Hlubší Koncepty:** [`docs/CONCEPTS.md`](./docs/CONCEPTS.md)

## 🧠 Příklady použití

### Orchestrace tvorby (CrewAI):
```bash
python3 -m core.consciousness_loop
```
### Kreativní brainstorming (AutoGen):
```bash
python3 -m agents.autogen_team
```

## 🧪 Testování

Systém je vybaven robustní sadou testů pro zajištění stability a spolehlivosti.

### Spuštění Testů
Pro spuštění kompletní sady testů (včetně unit a integračních testů) použijte následující příkaz z kořenového adresáře projektu:
```bash
PYTHONPATH=. pytest tests/
```
Tento příkaz automaticky najde a spustí všechny testy.

### Testovací Prostředí
Testy jsou navrženy tak, aby běžely v izolovaném prostředí bez nutnosti reálných API klíčů nebo produkční konfigurace. To je zajištěno mechanismem v `tests/conftest.py`, který automaticky:
1.  Nastaví proměnnou prostředí `SOPHIA_ENV=test`.
2.  Přiměje aplikaci načíst testovací konfiguraci z `config_test.yaml`.
3.  Mockuje veškerá volání na LLM, aby se zabránilo skutečným API dotazům.

Díky tomu jsou testy rychlé, spolehlivé a bezpečné.

## 🌐 Webové rozhraní (React UI)

Frontendová SPA aplikace je v adresáři `web/ui/`.

- Vývoj: viz `web/ui/README.md`
- Testování: `npm test` v `web/ui/` (Jest, Testing Library)
- Build: `npm run build` v `web/ui/`
- Hlavní komponenty: Chat, Login, Upload, Files, Profile, Notifications, Settings, Helpdesk, Language, RoleManager
- Komunikace s backendem přes REST API (`/api/`)

## 🛠️ Technologický Stack

-   **Jazyk:** Python
-   **AI Frameworky:** CrewAI, AutoGen, LangGraph, LangChain
-   **Backend:** FastAPI
-   **Frontend:** React (SPA, `web/ui/`)
-   **Databáze:** PostgreSQL
-   **Prostředí:** Git, Docker

----

*“Budoucnost se nepredikuje. Budoucnost se tvoří.”*

---

<p align="center">
  <strong>Visionary & Creator:</strong> Robert "kajobert" Kajzer | <strong>AI Architect:</strong> Nexus
</p>