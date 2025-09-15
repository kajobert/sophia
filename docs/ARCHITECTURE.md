### Autentizace a ochrana API – příklad toku

1. Uživatel klikne na „Přihlásit se“ (frontend).
2. Frontend přesměruje na `/api/login` (backend), backend zahájí OAuth2 flow (Google).
3. Po úspěšném přihlášení backend nastaví session cookie a přesměruje zpět na frontend.
4. Frontend zavolá `/api/me` a získá informace o uživateli (jméno, email, role).
5. Všechny chráněné endpointy (např. `/api/chat`) kontrolují session/token. Nepřihlášený uživatel dostane 401.
6. Odhlášení: frontend zavolá `/api/logout`, backend smaže session.

**Příklad volání:**

```http
GET /api/me
Cookie: session=... (nastaví backend po přihlášení)

HTTP/1.1 200 OK
{
    "name": "Jan Novák",
    "email": "jan.novak@gmail.com",
    "avatar": "https://..."
}
```

Nepřihlášený uživatel:

```http
GET /api/me

HTTP/1.1 401 Unauthorized
{
    "detail": "Not authenticated"
}
```
---

## Webové rozhraní (V4) – Návrh architektury

### Přehled

Webové rozhraní Sophia V4 je navrženo jako moderní, modulární a bezpečná platforma, která umožní uživatelům komunikovat se Sophií, spravovat svá data a v budoucnu rozšiřovat funkcionalitu (nahrávání souborů, notifikace, role, mobilní klienti atd.).

### Hlavní komponenty

- **Backend (API server):**
    - Framework: FastAPI (Python)
    - Autentizace: Google OAuth2 (přihlášení, identita, role)
    - API: REST + WebSocket (chat, správa souborů, uživatelé, notifikace, audit)
    - Správa session, bezpečnost, auditní logy
    - Připraveno na rozšíření o další endpointy (soubory, notifikace, profil, nastavení)
    - Navrženo pro multiplatformní použití (web, mobilní aplikace)

- **Frontend (Web klient):**
    - Framework: React (SPA, modularita, rozšiřitelnost)
    - Komponenty: přihlášení, chat, historie, nahrávání souborů (zatím nefunkční), správa dat, profil, nastavení, notifikace
    - Připraveno na i18n (vícejazyčnost), světlý/tmavý režim, rozšiřitelnost
    - Komunikace s backendem přes REST/WebSocket API

### Budoucí rozšiřitelnost

- **Nahrávání a správa souborů:**
    - Backend i frontend připraveny na upload, správu a analýzu uživatelských dat
- **Role a oprávnění:**
    - Možnost rozlišovat běžné uživatele, adminy, testery
- **Notifikace a zprávy:**
    - Systém pro upozornění na události, bezpečnostní hlášení, nové funkce
- **API pro mobilní aplikace:**
    - Stejné API použitelné pro web i mobilní klienty (Android/iOS)
- **Audit a bezpečnost:**
    - Logování akcí, auditní stopy, ochrana osobních údajů (GDPR)
- **i18n a UX:**
    - Připraveno na vícejazyčné rozhraní a UX vylepšení

### Schéma architektury

```
Uživatel <-> Frontend (React SPA) <-> Backend (FastAPI REST/WebSocket API) <-> Sophia Core/Agenti
```


### Build a testování webového UI

- Umístění: `web/ui/`
- Build: `npm run build`
- Testování: `npm test` (Jest, Testing Library)
- Hlavní komponenty: Chat, Login, Upload, Files, Profile, Notifications, Settings, Helpdesk, Language, RoleManager
- Komunikace s backendem přes REST API (`/api/`)

### Poznámky k implementaci

- Backend a frontend jsou oddělené projekty, komunikují přes API.
- Autentizace a session management řeší backend, frontend pouze získává tokeny a stav.
- Veškeré nové funkce (soubory, notifikace, role, mobilní klienti) lze přidat bez zásadních změn architektury.
- Dokumentace a datové modely budou od začátku navrženy s ohledem na verzování a rozšiřitelnost.

---
# Sophia V3 & V4 - Technická Architektura

Tento dokument popisuje technickou strukturu a komponenty systému Sophia.

---

## Architektura V3: Vědomé Jádro (Dokončeno)

Tato sekce popisuje základní architekturu, se kterou jsme dosáhli funkčního jádra.

### 1. Přehled Struktury Adresářů

sophia/
│
├── guardian.py             # "Strážce Bytí" - spouštěč a monitor
├── main.py                   # Hlavní smyčka Vědomí (cykly bdění/spánek)
├── config.yaml               # Centrální konfigurace
│
├── core/                     # Jádro Sophiiny mysli
│   ├── ethos_module.py       # Etické jádro a modul pro Koeficient Vědomí
│   └── consciousness_loop.py # Logika pro zpracování úkolů a sebereflexi
│
├── agents/                   # Definice specializovaných agentů
│
├── memory/                   # Paměťové systémy (SQLite, ChromaDB)
│
├── tools/                    # Nástroje dostupné pro agenty
│
├── web/                      # Rozhraní pro Tvůrce
...


### 2. Popis Klíčových Komponent V3

* **`guardian.py`**: Externí skript, který monitoruje `main.py` a v případě pádu provede `git reset`.
* **`main.py`**: Srdce Sophie s cykly "bdění" a "spánku".
* **`core/ethos_module.py`**: První verze etického jádra.
* **`memory/`**: Moduly pro práci s `SQLite` (epizodická) a `ChromaDB` (sémantická) pamětí.
* **`web/`**: Jednoduché API a UI pro zadávání úkolů.

---

## Architektura V4: Autonomní Tvůrce (V Vývoji)

Tato sekce popisuje cílovou architekturu pro další fázi vývoje, která staví na úspěších V3 a integruje pokročilé open-source technologie.

### 1. Cílová Adresářová Struktura V4

Struktura zůstává z velké části stejná, ale obsah a funkce klíčových modulů se dramaticky rozšiřují.

### 2. Evoluce Klíčových Komponent ve V4

* **`guardian.py` (Inteligentní Guardian)**:
    * **Technologie:** `psutil`
    * **Funkce:** Kromě reakce na pád bude proaktivně monitorovat zdraví systému (CPU, RAM) a provádět "měkké" restarty nebo varování, aby se předešlo selhání.

* **Komunikace a Databáze (Robustní Fronta)**:
    * **Technologie:** `PostgreSQL`, `psycopg2-binary`
    * **Funkce:** Nahradí `SQLite` jako hlavní databázi pro epizodickou paměť a úkolovou frontu. Tím se eliminuje problém se souběhem a umožní plynulá komunikace mezi `web/api.py` a `main.py` v reálném čase.

* **`memory/` (Pokročilá Paměť)**:
    * **Technologie:** Externí knihovna jako `GibsonAI/memori`
    * **Funkce:** Nahradí naši na míru psanou logiku pro váhu a blednutí vzpomínek za průmyslově ověřené řešení, které lépe spravuje životní cyklus informací.

* **`core/ethos_module.py` (Konstituční AI)**:
    * **Technologie:** `LangGraph`
    * **Funkce:** Přechází od jednoduchého porovnávání vektorů k sofistikovanému, dialogickému modelu etiky. Plány agentů projdou cyklem **kritiky** (porovnání s `DNA.md`) a **revize**, což vede k mnohem hlubšímu a bezpečnějšímu rozhodování.

* **`agents/` (Hybridní Agentní Model)**:
    * **Technologie:** `CrewAI` a `AutoGen`
    * **Funkce:** Systém bude využívat dva týmy agentů pro různé kognitivní funkce:
        * **Exekuční Tým (CrewAI):** Agenti jako `Planner`, `Engineer`, `Tester` budou fungovat v disciplinovaném, procesně orientovaném rámci `CrewAI` během fáze "Bdění" pro efektivní plnění úkolů.
        * **Kreativní Tým (AutoGen):** Agenti jako `Philosopher`, `Architect` budou fungovat ve flexibilním, konverzačním rámci `AutoGen` během fáze "Spánku" pro generování nových nápadů, sebereflexi a strategické plánování.

    * **LLM Integrace:**
        * Všichni agenti používají jednotný adapter `GeminiLLMAdapter` (viz `core/gemini_llm_adapter.py`), který zajišťuje robustní a snadno vyměnitelnou integraci s Google Gemini API.
        * Adapter je inicializován v `core/llm_config.py` dle konfigurace v `config.yaml` a předáván agentům jako `llm=llm`.
        * Přepnutí na jiného providera (např. OpenAI, LangChain) je možné úpravou konfigurace a jednoho řádku v `llm_config.py`.


* **`/sandbox` (Izolované Prostředí)**:
    * **Funkce:** Bezpečný a izolovaný adresář, kde mohou agenti volně vytvářet, upravovat a spouštět soubory a kód, aniž by ovlivnili zbytek systému. Slouží jako testovací pole pro všechny tvůrčí úkoly.

* **`tools/` (Dílna pro Tvůrce)**:
    * **Technologie:** Vlastní implementace
    * **Funkce:** Bude obsahovat nové, klíčové nástroje pro agenty, jako `FileSystemTool` (pro práci se soubory v `/sandbox`) a `CodeExecutorTool` (pro spouštění a testování kódu).

* **`core/gemini_llm_adapter.py` (LLM Adapter):**
    * **Technologie:** `google-generativeai`
    * **Funkce:** Zajišťuje jednotné rozhraní pro všechny agenty a snadnou rozšiřitelnost na další LLM providery.

