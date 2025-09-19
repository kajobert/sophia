# 🗺️ Detailní Roadmapa k MVP: Sophia jako Autonomní AI Vývojář

Tento dokument definuje technicky propracovaný a proveditelný plán, který nás co nejrychleji dovede k **Minimum Viable Product (MVP)**.

## 🎯 Cíl a Definice MVP

Cílem MVP je: **"Sophia jako autonomní AI vývojář."**

To znamená, že Sophia musí být schopna:
- [ ] **Přijmout úkol:** Přes své webové rozhraní přijmout úkol v přirozeném jazyce.
- [ ] **Naplánovat řešení:** Úkol pochopit a vytvořit strojově čitelný plán kroků.
- [ ] **Provést plán:** Použít sadu nástrojů (práce se soubory, terminál, Git) k realizaci plánu.
- [ ] **Ověřit práci:** Spustit testy a analyzovat jejich výsledek.
- [ ] **Iterovat a opravit:** V případě neúspěchu analyzovat chybu a pokusit se o opravu.
- [ ] **Dokončit a odevzdat:** Po úspěšném dokončení svou práci commitnout do nové větve v repozitáři.

---

## EPIC 1: Autonomní Nástroje a Interakce s Prostředím ("Ruce")

**Cíl:** Vybavit Sophii spolehlivými a unifikovanými nástroji pro práci se souborovým systémem, shellem a Gitem.

### Klíčové technické úkoly:

- [ ] **Sjednocení nástrojů pod `BaseTool`:**
    *   **Co:** Vytvoření abstraktní třídy `BaseTool` v `tools/base_tool.py`.
    *   **Proč:** Zajistí jednotné rozhraní pro všechny nástroje, což zjednoduší jejich správu a používání orchestrátorem.
    *   **Jak:** Třída bude definovat metodu `execute(**kwargs) -> str`. Všechny stávající nástroje v adresáři `/tools` (např. `code_executor.py`, `file_system.py`) budou upraveny, aby z této třídy dědily.

- [ ] **Implementace robustního `GitTool`:**
    *   **Co:** Vytvoření nového nástroje `tools/git_tool.py`.
    *   **Proč:** Poskytne Sophii klíčovou schopnost spravovat verze kódu, což je základní předpoklad pro autonomní vývoj.
    *   **Jak:** Nástroj bude postaven na knihovně `gitpython` a bude obsahovat metody pro základní Git operace: `clone`, `status`, `add`, `commit`, `push` a `create_branch`.

- [ ] **Dynamické zpřístupnění nástrojů agentům:**
    *   **Co:** Mechanismus pro informování agentů o dostupných nástrojích.
    *   **Proč:** Agenti musí vědět, jaké nástroje mají k dispozici a jak je správně volat.
    *   **Jak:** Orchestrátor při startu dynamicky načte všechny třídy dědící z `BaseTool`. Jejich instance (spolu s popisem jejich účelu a parametrů) budou předány agentům v rámci `SharedContext`.

---

## EPIC 2: Kognitivní Cyklus a Řešení Problémů ("Mozek")

**Cíl:** Umožnit Sophii plánovat, provádět a iterativně opravovat komplexní úkoly.

### Klíčové technické úkoly:

- [ ] **Strojově čitelný formát plánu (JSON):**
    *   **Co:** Definice standardizovaného formátu pro plány generované `PlannerAgentem`.
    *   **Proč:** Strukturovaný plán je nutný pro spolehlivé provádění a monitorování ze strany orchestrátoru.
    *   **Jak:** Plán bude pole kroků (JSON array of objects). Každý krok bude objekt s klíči: `step_id`, `description` (popis pro člověka), `tool_name` (název nástroje k použití), `parameters` (slovník s parametry pro nástroj) a `expected_outcome` (očekávaný výsledek).

- [ ] **Implementace cyklu "Pokus-Omyl-Oprava" v Orchestrátoru:**
    *   **Co:** Rozšíření logiky v `core/orchestrator.py`.
    *   **Proč:** Umožní Sophii autonomně reagovat na chyby (např. selhání testů) a pokusit se je opravit, což je jádrem její inteligence.
    *   **Jak:** Orchestrátor bude provádět kroky plánu. Po každém kroku zanalyzuje výstup (návratový kód, logy). Pokud detekuje chybu, přeruší provádění, zabalí chybovou hlášku a poslední stav do kontextu a znovu zavolá `PlannerAgent` s instrukcí: "Plán selhal s touto chybou, navrhni opravu."

- [ ] **Rozšíření sdíleného kontextu (`SharedContext`):**
    *   **Co:** Přidání nových polí do datové struktury `SharedContext` v `core/context.py`.
    *   **Proč:** Zajištění efektivního a bezstavového předávání informací mezi jednotlivými agenty a cykly.
    *   **Jak:** Objekt bude rozšířen o: `current_plan` (JSON plán), `step_history` (seznam provedených kroků a jejich výsledků), `last_step_output` (detailní výstup posledního kroku) a `available_tools` (seznam dostupných nástrojů).

---

## EPIC 3: Interaktivní Rozhraní a Komunikace ("Hlas a Uši")

**Cíl:** Umožnit plnohodnotnou obousměrnou komunikaci mezi uživatelem a Sophií.

### Klíčové technické úkoly:

- [ ] **Rozšíření API o endpointy pro správu úkolů:**
    *   **Co:** Implementace nových endpointů v `web/api/main.py`.
    *   **Proč:** Poskytne uživatelskému rozhraní potřebné háčky pro zadávání úkolů a sledování jejich postupu.
    *   **Jak:**
        *   `POST /tasks`: Přijme popis úkolu v přirozeném jazyce, vrátí unikátní `task_id`.
        *   `GET /tasks/{task_id}`: Vrátí aktuální stav úkolu, včetně kompletního plánu, historie provedených kroků a jejich výsledků.
        *   `GET /tasks/{task_id}/ws`: WebSocket endpoint pro real-time komunikaci.

- [ ] **Real-time notifikace pomocí WebSockets:**
    *   **Co:** Integrace `FastAPI WebSocket` do `web/api/main.py`.
    *   **Proč:** Poskytne uživateli okamžitou zpětnou vazbu o tom, co Sophia právě dělá.
    *   **Jak:** Po každém dokončeném kroku v orchestrátoru bude přes WebSocket odeslána zpráva (JSON) obsahující `step_id`, `description` a `status` (např. `success`, `failure`).

- [ ] **Prezentace výsledků v UI:**
    *   **Co:** Návrh datových struktur, které API poskytne frontendu.
    *   **Proč:** Aby UI mohlo srozumitelně a přehledně zobrazit výsledky práce Sophie.
    *   **Jak:** Endpoint `GET /tasks/{task_id}` bude vracet data strukturovaná pro snadné zobrazení: seznam změněných souborů (z výstupu `GitTool`), výstup z testů (z `CodeExecutorTool`) a po úspěšném dokončení i odkaz na finální commit.

---

## EPIC 4: Profesionalizace a Vývojářská Zkušenost (DX)

**Cíl:** Aplikovat osvědčené postupy pro zajištění dlouhodobé udržitelnosti, kvality a snadného zapojení nových vývojářů (lidských i AI).

### Klíčové technické úkoly:

- [ ] **Vytvoření `DEVELOPER_GUIDE.md`:**
    *   **Co:** Vytvoření nebo rozšíření klíčového dokumentu pro vývojáře v `docs/DEVELOPER_GUIDE.md`.
    *   **Proč:** Snížení bariéry pro vstup nových přispěvatelů a sjednocení postupů.
    *   **Jak:** Dokument bude obsahovat sekce inspirované `DESIGN_SUMMARY.md`: "První spuštění a nastavení prostředí", "Popis architektury a struktury projektu", "Jak přidat nového agenta/nástroj" a "Code Review Checklist".

- [ ] **Základní CI/CD pipeline (GitHub Actions):**
    *   **Co:** Vytvoření souboru `.github/workflows/ci.yml`.
    *   **Proč:** Automatizace kontroly kvality kódu při každém commitu.
    *   **Jak:** Pipeline bude definovat workflow, které se spustí na každý pull request a bude obsahovat následující kroky:
        1.  Checkout kódu.
        2.  Nastavení prostředí Pythonu.
        3.  Instalace závislostí pomocí `uv -r requirements.txt`.
        4.  Spuštění linteru (např. `ruff` nebo `flake8`).
        5.  Spuštění sady testů pomocí `pytest`.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
