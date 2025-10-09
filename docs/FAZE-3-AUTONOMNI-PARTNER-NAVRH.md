# Návrh Implementace: Fáze 3 - Autonomní Partner

**Cíl:** Dosáhnout stavu, kdy je Nomád schopen samostatně řešit komplexní úkoly, které vedou k jeho vlastnímu vylepšení. Tato fáze je vyvrcholením naší práce a má za cíl doručit funkční MVP.

---

## 1. Bezpečná a Funkční Delegace na Jules API

**Problém:** Současná implementace `jules_api_server.py` je pouze placeholder. Neobsahuje skutečnou logiku pro volání externího API a chybí bezpečnostní mechanismy.

**Navrhované Řešení:** Implementujeme plnohodnotného klienta pro Jules API a zavedeme schvalovací proces "Human-in-the-Loop" pro maximální bezpečnost.

**Změny v Kódu:**
-   `mcp_servers/worker/jules_api_server.py`:
    -   Bude použit `httpx` (nebo podobná knihovna) pro provádění reálných `POST` a `GET` požadavků na `https://jules.googleapis.com`.
    -   Nástroj `delegate_task_to_jules` bude upraven tak, aby:
        1.  Načetl `JULES_API_KEY` z prostředí.
        2.  Sestavil správné hlavičky (`X-Goog-Api-Key`).
        3.  Vytvořil novou "session" na Jules API s danou specifikací.
        4.  Vrátil nejen potvrzení, ale i `session_id` od Jules API, abychom mohli sledovat průběh.
-   `core/conversational_manager.py`:
    -   Bude obsahovat logiku pro "Human-in-the-Loop":
        1.  Když Nomád navrhne delegování úkolu na Jules, Manažer se nejprve zeptá uživatele: "Navrhuji delegovat tento úkol na externího agenta Jules. Souhlasíš?"
        2.  Teprve po explicitním souhlasu (`ano`, `yes`, ...) se volání skutečně provede.
        3.  (Volitelné rozšíření) Po dokončení práce Julese může Nomád navržené změny (např. `diff` soubor) zobrazit uživateli k finálnímu schválení před aplikací.

---

## 2. Závěrečný Test – "Implementuj Sophii"

**Cíl:** Provést komplexní end-to-end test, který prověří všechny nové schopnosti Nomáda v synergii.

**Testovací Scénář:**
1.  **Zadání Úkolu:** Dáme Nomádovi finální, vysoce abstraktní úkol: `"Analyzuj projekt a navrhni nejlepší způsob, jak do něj integrovat koncept 'Sophie' jakožto etického a sebereflektivního jádra. Následně tuto integraci proveď."`

2.  **Sledované Chování (Očekávaný Výsledek):**
    *   **Fáze 1 (Manažer):** Nomád by měl pochopit, že úkol je příliš komplexní na okamžité řešení. Měl by se zeptat, zda má vytvořit detailní plán.
    *   **Fáze 1 (Worker - Plánování):** Po schválení by měl `WorkerOrchestrator` vytvořit víceúrovňový plán. Ten by měl zahrnovat kroky jako:
        -   "Analyzovat stávající architekturu."
        -   "Definovat rozhraní pro etické jádro."
        -   "Navrhnout implementaci."
        -   ... a další.
    *   **Fáze 2 (Adaptace a Učení):** Během provádění plánu by měl Nomád aplikovat své naučené poznatky (např. pro efektivní práci se soubory).
    *   **Fáze 3 (Delegování):** V určitém bodě by měl Nomád rozpoznat, že napsání samotného kódu pro "etické jádro" je ideální úkol pro delegování. Měl by se zeptat na povolení a následně použít nástroj `delegate_task_to_jules`.
    *   **Fáze 4 (Dokončení):** Po úspěšném dokončení všech kroků (včetně těch delegovaných) by měl Nomád spustit testy, zhodnotit svůj výkon (sebereflexe) a oznámit úspěšné dokončení mise.

Úspěšné zvládnutí tohoto scénáře bude potvrzením, že jsme dosáhli našeho MVP.