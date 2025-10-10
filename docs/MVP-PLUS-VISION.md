# Návrh Rozšíření MVP: Cesta k Plně Autonomnímu Partnerství

**Verze:** 1.0
**Datum:** 2025-10-10
**Autor:** Sophia (na základě dialogu s Robertem)

Tento dokument navazuje na `MVP-VISION-AND-ARCHITECTURE.md` a specifikuje dodatečné schopnosti a architektonické úpravy nutné k přechodu od MVP k vizi plně integrovaného a autonomního AI partnera, který operuje v jednotném rozhraní.

---

## 1. Cílový Stav: Jednotné a Autonomní Prostředí

Cílem je eliminovat potřebu uživatele manuálně interagovat s různými platformami (lokální VS Code, `gemini.google.com`, `jules.google.com`, GitHub). Veškerá interakce probíhá skrze jediné rozhraní (TUI/Web UI), kde uživatel zadává úkoly, poskytuje inspiraci a funguje jako "Human-in-the-Loop" pro schvalování a řešení problémů, na které agent narazí.

## 2. Chybějící Komponenty v Aktuálním MVP Plánu

Pro dosažení výše popsaného stavu je nutné stávající MVP plán rozšířit o následující čtyři klíčové oblasti:

### 2.1. Hluboká Integrace s Externími Službami

Agent musí získat schopnost plně zastoupit uživatele při interakci s klíčovými vývojářskými platformami.

* **Nástroje pro GitHub API:**
    * **Specifikace:** Implementovat sadu nástrojů (např. v `tools/github_tools.py`), které umožní agentovi:
        * `create_pull_request(title: str, body: str, head_branch: str, base_branch: str)`: Vytvořit Pull Request po dokončení práce.
        * `get_pull_request_status(pr_number: int)`: Zjišťovat stav PR (např. probíhající CI testy).
        * `list_issues()`: Proaktivně zjišťovat nové úkoly.
    * **Přínos:** Agent bude schopen samostatně dokončit celý vývojový cyklus od zadání až po odeslání kódu k revizi.

* **Nástroje pro Monitoring Jules API:**
    * **Specifikace:** Vytvořit nástroje pro asynchronní práci s `jules.google.com`:
        * `get_jules_task_status(task_id: str)`: Periodicky se dotazovat na stav delegovaného úkolu.
        * `get_jules_task_result(task_id: str)`: Po dokončení úkolu stáhnout jeho výsledek (např. `diff` soubor nebo kód).
    * **Přínos:** Skutečná, autonomní delegace, kde agent nezůstane "viset" čekáním, ale aktivně monitoruje a zpracovává výsledky.

### 2.2. Architektura pro Dlouhotrvající Úkoly

Současná architektura je vázána na životní cyklus TUI aplikace. Pro plnou autonomii je nutné toto oddělit.

* **"Headless" Režim Běhu Agenta:**
    * **Specifikace:** Refaktorovat `ConversationalManager` a `WorkerOrchestrator` tak, aby mohly běžet jako nezávislý "daemon" (služba na pozadí). TUI nebo Web UI se k tomuto běžícímu jádru budou připojovat jako klienti (např. přes WebSocket nebo API).
    * **Přínos:** Agent může pracovat na komplexním úkolu několik hodin nebo dní, i když uživatel zavře své lokální rozhraní. Po opětovném připojení se uživateli zobrazí aktuální stav práce.

### 2.3. Proaktivní Vnímání a Iniciativa

Agent nesmí být pouze reaktivní. Musí získat schopnost proaktivně monitorovat své prostředí a přicházet s vlastními návrhy.

* **Nástroje pro "Vnímání" Projektu:**
    * **Specifikace:** Vytvořit sadu nástrojů, které se mohou spouštět na základě časovače nebo události:
        * `check_git_status()`: Periodicky kontroluje, zda v repozitáři nejsou necommitnuté změny.
        * `check_github_activity()`: Sleduje novou aktivitu na GitHubu (nové issues, komentáře v PR).
    * **Přínos:** Agent se stane skutečným partnerem, který dokáže upozornit na potenciální problémy ("Všimla jsem si, že máš v projektu změny, které nejsou commitnuté. Chceš, abych je uložila?") nebo navrhnout novou práci.

### 2.4. Pokročilý Model Interakce "Human-in-the-Loop"

Když agent narazí na problém, interakce musí být efektivní a vést k rychlému řešení.

* **Dialogické Řešení Problémů:**
    * **Specifikace:** Architektura musí podporovat "párové programování". Když agent narazí na chybu (např. selhání testů), musí být schopen:
        1.  Zastavit exekuci.
        2.  Upozornit uživatele a zobrazit mu relevantní kontext (chybovou hlášku, kód, který selhal).
        3.  Přijmout od uživatele návrh na opravu (např. textový popis nebo přímo kód).
        4.  Aplikovat navrženou změnu a pokračovat v exekuci.
    * **Přínos:** Místo pouhého "poraď mi" se interakce změní na efektivní spolupráci, kde uživatel pomáhá agentovi překonat překážku a agent se z této interakce učí pro příště.