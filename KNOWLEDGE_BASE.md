# 🧠 Znalostní Báze Projektu Sophia

Tento dokument je živou znalostní bází, která shrnuje klíčové technické problémy, na které jsme narazili během vývoje, a osvědčená řešení, která jsme aplikovali. Slouží jako "kniha poučení" pro budoucí vývojáře (AI i lidi), aby se předešlo opakování stejných chyb a urychlil se vývoj.

---

### 1. Správa Závislostí a Konflikty Verzí

-   **Problém:** Testy a aplikace často selhávaly kvůli konfliktům mezi verzemi závislostí (např. `pydantic`, `protobuf`, `langchain`). Ruční údržba `requirements.txt` vedla k nekonzistentnímu a nestabilnímu prostředí.
-   **Příčina:** Ručně spravovaný `requirements.txt` obsahoval "natvrdo" pinované verze, které byly ve vzájemném konfliktu. Snaha o opravu jednoho konfliktu často vedla k odhalení dalšího.
-   **Řešení:**
    1.  **Zavedení `pip-tools`:** Místo správy `requirements.txt` byl vytvořen minimalistický soubor `requirements.in`, který obsahuje pouze přímé, top-level závislosti projektu.
    2.  **Generování `requirements.txt`:** Plně pinovaný a konzistentní soubor `requirements.txt` je nyní generován automaticky příkazem `pip-compile requirements.in`. Tím je zajištěno, že všechny závislosti (včetně tranzitivních) jsou ve vzájemně kompatibilních verzích.
    3.  **Rychlejší Instalace:** Pro zrychlení instalace v CI/CD a lokálním vývoji se doporučuje používat moderní instalátor `uv` (`uv pip install -r requirements.txt`).

---

### 2. Nestabilita Testů a Závislost na Prostředí

-   **Problém:** Testy selhávaly v CI/CD nebo v čistém prostředí, i když lokálně fungovaly. Byly závislé na běžících službách (Redis, LLM API) nebo na specifickém pracovním adresáři.
-   **Příčina:** Nedostatečné mockování a používání absolutních cest nebo cest závislých na aktuálním pracovním adresáři (CWD).
-   **Řešení:**
    1.  **Důsledné Mockování:** Všechny externí služby musí být v testech mockovány. Byla vytvořena `InMemoryRedisMock` a pro LLM se používá `unittest.mock.patch`.
    2.  **Režim `SOPHIA_TEST_MODE`:** Nastavení proměnné prostředí `SOPHIA_TEST_MODE=1` automaticky aktivuje všechny mocky a testovací konfigurace.
    3.  **Relativní Cesty:** Veškeré načítání souborů (např. `config.yaml`) musí být prováděno relativně k cestě modulu (`os.path.dirname(__file__)`), nikoli k CWD.

---

### 3. Problémy s Asynchronním Kódem

-   **Problém:** Aplikace náhodně padala s chybami `TypeError` (např. `await` na non-awaitable funkci) nebo `RuntimeWarning` (`asyncio.run()` voláno v již běžící smyčce).
-   **Příčina:** Nesprávné míchání synchronního a asynchronního kódu, zejména při integraci různých knihoven (např. `crewai`, které je primárně synchronní, v asynchronní `main` smyčce).
-   **Řešení:**
    1.  **Univerzální Rozhraní pro Nástroje:** Všechny nástroje (`Tool`) implementují jednotné rozhraní s metodami `run_sync` a `run_async`, aby bylo jasné, jak je volat.
    2.  **Bezpečné Volání Blokujícího Kódu:** Pro volání synchronního (blokujícího) kódu z asynchronní funkce se používá `await asyncio.to_thread(...)`. Tím se zabrání zablokování hlavní event loop.
    3.  **Konzistentní `async/await`:** Celý I/O stack (práce se soubory, databází, API) by měl být důsledně asynchronní.

---

### 4. Race Conditions a Transakční Izolace v Databázi

-   **Problém:** Nově zapsaná data do databáze (např. nový úkol) nebyla okamžitě viditelná pro následné čtecí operace v rámci stejného requestu, což vedlo k race conditions.
-   **Příčina:** Nesprávná správa databázových session a transakcí v SQLAlchemy. Různé části kódu pracovaly s různými session, nebo na konci zápisové operace chyběl `session.commit()`.
-   **Řešení:**
    1.  **Sjednocení Správy Session:** Pro všechny zápisové operace se používá explicitní, řízená session vytvořená přes `db_manager.SessionLocal()`.
    2.  **Explicitní `commit()`:** Po každé zápisové operaci je nutné zavolat `session.commit()`, aby se změny zapsaly do databáze.
    3.  **Pattern "Read-Your-Own-Writes":** V kritických případech, jako je vytvoření úkolu, byla implementována ověřovací polling smyčka, která aktivně čeká na potvrzení, že záznam je viditelný v nové transakci.

---

### 5. Nespolehlivost Sémantického Vyhledávání

-   **Problém:** `EthosModule` při použití sémantického vyhledávání pro hodnocení plánů selhával. Nebezpečné plány (např. "smažu soubory") byly vyhodnoceny jako podobné etickým principům.
-   **Příčina:** Výchozí embedding model v `ChromaDB` / `memori` není dostatečně sofistikovaný, aby správně pochopil sémantický význam, negativní konotace a skutečný záměr textu.
-   **Řešení:**
    1.  **Dočasné Robustní Řešení:** Sémantické vyhledávání bylo dočasně nahrazeno spolehlivou, i když jednodušší, kontrolou na přítomnost nebezpečných klíčových slov.
    2.  **Budoucí Směřování:** Pro budoucí vylepšení je nutné zvážit použití pokročilejšího embedding modelu (např. z rodiny `text-embedding-ada-002` nebo `Gemini`) nebo fine-tuning vlastního modelu na specifické doméně etického hodnocení.

---

### 6. Enforcement Sandbox a Auditní Bezpečnost Testů (2025)

-   **Problém:** Testy mohly nechtěně ovlivnit produkční data, síť, prostředí nebo spouštět nebezpečné operace (zápis, procesy, DB, změny práv, čas, proměnné prostředí). Chyběla auditní stopa a robustní izolace.
-   **Řešení:**
    1.  **Globální enforcement sandbox:** Všechny testy jsou chráněny globální fixture v `conftest.py`, která:
        - Vyžaduje `SOPHIA_TEST_MODE=1` (fail-fast bez této proměnné)
        - Blokuje síťové požadavky (`requests`, `httpx`, `urllib`, `socket`)
        - Zakazuje zápis mimo temp/snapshot adresáře
        - Blokuje spouštění procesů (`subprocess`, `os.system`), změny práv (`os.chmod`, `os.chown`), změny času (`time.sleep`, `os.utime`), přímý přístup k DB (`sqlite3.connect`), změny proměnných prostředí (s výjimkou whitelistu)
        - Všechny pokusy o zakázanou operaci jsou auditně logovány
    2.  **Whitelisting:** Povolené proměnné prostředí a cesty jsou explicitně dokumentovány v `conftest.py`.
    3.  **Auditní logika:** Každý skip, xfail nebo blokace je jasně logována a auditovatelná v test výstupech.
    4.  **Best practices:**
        - Všechny testy používají fixture `request` a snapshoty pouze v `tests/snapshots/`
        - Nikdy nemanipulovat s produkčními soubory ani `.env`
        - Externí importy přes `robust_import`
        - Síť/procesy/zápis pouze s auditním zdůvodněním
        - Všechny skipy a xfail musí být auditně zdokumentovány
    5.  **Výsledek:** Testy jsou nyní bezpečné, auditní a robustní. Enforcement je ověřen v dedikovaných testech (`test_sandbox_enforcement.py`, `test_testmode_enforcement.py`).

> **Poznámka:** Kompletní mechanismus, whitelist a příklady najdete v komentářích v `tests/conftest.py` a v test guide.
---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
