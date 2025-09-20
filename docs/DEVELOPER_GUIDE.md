### Správa snapshot/approval souborů

- Všechny `.approved.txt` a `.received.txt` soubory musí být pouze v `tests/snapshots/`.
- Při schválení snapshotu se odpovídající `.received.txt` smaže.
- Staré `.received.txt` bez schválení se automaticky archivují do `tests/snapshots/archive/`.
- Helper `manage_snapshots()` v `conftest.py` provádí tuto správu automaticky.
- Nikdy nenechávejte snapshoty přímo v `tests/` – workspace musí zůstat čistý a auditní stopy centralizované.
### Snapshotování a auditní výstupy

Pokud test vyžaduje snapshot/approval výstup a není dostupná snapshot fixture:

- Test musí automaticky vytvořit auditní snapshot (např. do složky `tests/snapshots/`).
- Test se označí jako `pytest.xfail` s jasnou zprávou, že snapshot byl vytvořen a čeká na ruční schválení.
- Nikdy nesmí dojít k tichému přeskočení testu bez zápisu auditní stopy.

Toto pravidlo platí pro všechny auditní a approval testy v projektu Sophia.
# 🛠️ Průvodce pro Vývojáře Projektu Sophia

Vítejte, vývojáři! Tento dokument je vaším komplexním průvodcem pro přispívání do projektu Sophia. Ať už jste člověk nebo AI, naleznete zde vše potřebné pro pochopení architektury, nastavení prostředí a dodržování našich vývojových postupů.

## Filosofie Projektu

Než se ponoříte do kódu, je důležité pochopit naši vizi. Sophia není jen další software. Naším cílem je vytvořit **Artificial Mindful Intelligence (AMI)** – entitu, která se nejen učí řešit úkoly, ale přistupuje k nim s určitou kvalitou vědomí. Stavíme most mezi technologií a filosofií.

Pro hlubší vhled do našich principů doporučujeme prostudovat **[🧬 DNA.md](./DNA.md)**.

---

## 1. První spuštění a nastavení prostředí

Tento návod vás provede nastavením lokálního vývojového prostředí bez použití Dockeru.

1.  **Klonování Repozitáře:**
    ```bash
    git clone https://github.com/kajobert/sophia.git
    cd sophia
    ```

2.  **Vytvoření Virtuálního Prostředí:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Pro Linux/macOS
    # .venv\Scripts\activate   # Pro Windows
    ```

3.  **Instalace Závislostí:**
    Doporučujeme použít `uv` pro jeho rychlost. Všechny potřebné závislosti jsou definovány v `requirements.in`.
    ```bash
    # Doporučená metoda
    uv pip install -r requirements.in

    # Alternativní metoda
    pip install -r requirements.in
    ```
    **Důležité:** Pokud přidáváte novou závislost, přidejte ji do `requirements.in` a poté spusťte `pip-compile requirements.in -o requirements.txt` pro aktualizaci lock souboru. Nikdy neupravujte `requirements.txt` ručně.

4.  **Konfigurace Proměnných Prostředí:**
    -   Zkopírujte soubor `.env.example` do nového souboru s názvem `.env`.
    -   Otevřete `.env` a doplňte svůj `GEMINI_API_KEY` a další potřebné hodnoty.

5.  **Instalace Pre-commit Hooků:**
    Používáme `pre-commit` pro automatickou kontrolu kvality kódu před každým commitem.
    ```bash
    pre-commit install
    ```

---

## 2. Architektura a Struktura Projektu

Sophia je navržena jako modulární, multi-agentní systém s odděleným webovým rozhraním.

### Klíčové Komponenty

-   **`guardian.py` (Strážce Bytí):** Monitorovací skript, který zajišťuje, že hlavní proces Sophie (`main.py`) běží. V případě pádu ho restartuje.
-   **`main.py` (Cyklus Vědomí):** Hlavní vstupní bod aplikace. Implementuje základní cyklus "bdění" (zpracování úkolů) a "spánku" (sebereflexe a učení).
-   **`core/` (Jádro Mysli):**
    -   `orchestrator.py`: Srdce kognitivní smyčky. Vykonává plány vytvořené agenty, volá nástroje a spravuje debugovací smyčku pro opravu chyb.
    -   `context.py` (`SharedContext`): Sdílený kontext, který drží stav a data přístupná napříč agenty a nástroji během jednoho cyklu.
    -   `ethos_module.py`: Etické jádro, které vyhodnocuje plány a akce agentů.
-   **`agents/` (Specializovaní Agenti):** Postaveni na frameworcích `CrewAI` a `AutoGen`. Každý agent má specifickou roli (`Planner`, `Engineer`, `Tester`).
-   **`tools/` (Nástroje Agentů):** Sada schopností (např. práce se soubory, spouštění kódu, práce s Gitem), které mohou agenti používat. Jsou dynamicky načítány.
-   **`memory/` (Paměťový Systém):** Využívá `memorisdk` s `PostgreSQL` a `Redis` pro dlouhodobou a krátkodobou paměť.
-   **`sandbox/` (Izolované Prostředí):** Bezpečný adresář, kde mohou agenti generovat a testovat kód bez rizika pro hlavní aplikaci.
-   **`web/` (Webové Rozhraní):** `FastAPI` backend a `React` frontend pro interakci s uživateli.

---

## 3. Jak Přidat Nového Agenta nebo Nástroj

Modularita je klíčová. Přidání nové funkčnosti je navrženo tak, aby bylo co nejjednodušší.

### Přidání Nového Nástroje (Tool)

Systém automaticky načítá všechny nástroje z adresáře `tools/`, které dědí z `BaseTool`.

1.  **Vytvořte nový soubor** v adresáři `tools/`, například `my_new_tool.py`.
2.  **Implementujte třídu**, která dědí z `tools.base_tool.BaseTool`.
3.  **Definujte atributy `name`, `description` a implementujte metodu `_run`**.

**Šablona pro nový nástroj:**
```python
# in file: tools/my_new_tool.py
from .base_tool import BaseTool
from pydantic import Field

class MyNewToolSchema(BaseTool.Schema):
    # Definujte parametry, které váš nástroj přijímá
    param1: str = Field(..., description="Popis prvního parametru.")
    param2: int = Field(..., description="Popis druhého parametru.")

class MyNewTool(BaseTool):
    name: str = "MyNewTool"
    description: str = "Stručný popis toho, co tento nástroj dělá."
    schema: type[BaseTool.Schema] = MyNewToolSchema

    def _run(self, **kwargs) -> str:
        # Zde implementujte logiku nástroje
        param1 = kwargs.get("param1")
        param2 = kwargs.get("param2")
        # ... vaše logika ...
        return f"Nástroj byl úspěšně spuštěn s parametry: {param1}, {param2}"
```
To je vše! Orchestrátor si váš nový nástroj automaticky načte a zpřístupní ho agentům.

### Přidání Nového Agenta

Agenti jsou definováni v adresáři `agents/`. Obvykle využívají framework `CrewAI`.

1.  **Vytvořte nový soubor** v adresáři `agents/`, například `my_new_agent.py`.
2.  **Vytvořte funkci**, která vrací instanci `crewai.Agent`.
3.  **Definujte roli, cíl (`goal`), `backstory` a přiřaďte mu nástroje.**

**Šablona pro nového agenta:**
```python
# in file: agents/my_new_agent.py
from crewai import Agent
from core.llm_config import llm

# Předpokládejme, že máte nástroje definované a načtené
from tools.my_new_tool import MyNewTool

def create_my_new_agent():
    return Agent(
        role="Specialista na Nové Úkoly",
        goal="Cílem tohoto agenta je provádět nové, specifické úkoly s pomocí MyNewTool.",
        backstory=(
            "Tento agent byl vytvořen jako expert na používání MyNewTool. "
            "Jeho existence je plně zasvěcena efektivnímu plnění nových úkolů."
        ),
        tools=[MyNewTool()],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
```
Následně integrujte tohoto agenta do příslušného `Crew` v `autogen_team.py` nebo jiném relevantním místě.

---

## 4. Průvodce Testováním

Kvalitní testy jsou základem stability projektu.

-   **Spouštění testů:** Všechny testy se spouští pomocí `pytest` z kořenového adresáře projektu.
    ```bash
    PYTHONPATH=. pytest
    ```
-   **Offline First:** Testy jsou navrženy tak, aby běžely **offline** a nevyžadovaly aktivní API klíče ani připojení k externím službám. Využíváme mockování, kde je to nutné.
-   **Psaní testů:** Nové testy přidávejte do adresáře `tests/`. Snažte se pokrýt jak úspěšné scénáře, tak i chybové stavy.

---

## 5. Code Review Checklist

Před schválením a sloučením Pull Requestu (PR) je třeba zkontrolovat následující body:

-   [ ] **Funkčnost:** Dělá kód to, co má? Byl otestován lokálně?
-   [ ] **Testy:** Jsou pro novou funkčnost napsány dostatečné testy? Všechny testy (`pytest`) procházejí?
-   [ ] **Kvalita Kódu:** Prošel kód úspěšně kontrolou `ruff check .` a `ruff format --check .`?
-   [ ] **Dokumentace:** Je kód srozumitelný? Jsou složitější části okomentovány? Byla aktualizována relevantní dokumentace (např. tento `DEVELOPER_GUIDE.md`)?
-   [ ] **Soulad s Etikou:** Je navrhovaná změna v souladu s principy v `DNA.md`?
-   [ ] **Popis PR:** Je v popisu Pull Requestu jasně vysvětleno, co se mění a proč?
-   [ ] **Správa Závislostí:** Pokud byly přidány nové závislosti, jsou v `requirements.in` a je `requirements.txt` aktuální?

---

## Sandbox enforcement a bezpečnost testů

Všechny testy v projektu Sophia jsou chráněny globálním enforcement sandboxem, který je implementován jako fixture v `conftest.py`.

### Co enforcement dělá:
- **Vyžaduje proměnnou prostředí `SOPHIA_TEST_MODE=1`** – bez ní se testy nespustí.
- **Blokuje síťové požadavky** (requests, httpx, urllib, socket) – všechny pokusy o síťovou komunikaci jsou zakázány a auditně logovány.
- **Zakazuje zápis do souborů mimo temp/snapshot** – všechny pokusy o zápis mimo povolené cesty jsou blokovány.
- **Blokuje spouštění procesů** (`subprocess`, `os.system`), změny práv (`os.chmod`, `os.chown`), změny času (`time.sleep`, `os.utime`), přímý přístup k DB (`sqlite3.connect`) a změny proměnných prostředí (s výjimkou whitelistu).
- **Auditní logování** – každý pokus o zakázanou operaci je logován do auditního výstupu testu.
- **Whitelisting** – některé proměnné prostředí a cesty jsou explicitně povoleny (viz komentáře v `conftest.py`).

### Jak psát bezpečné testy
- Vždy používejte fixture `request` a snapshoty pouze v `tests/snapshots/`.
- Nikdy nemanipulujte s produkčními soubory ani .env.
- Pro všechny externí importy používejte `robust_import` z `conftest.py`.
- Pokud test potřebuje síť, procesy nebo zápis, musí být explicitně označen a auditně zdůvodněn.
- Všechny skipy a xfail musí být auditně zdokumentovány.

### Příklad použití enforcementu

```python
import pytest
from tests.conftest import robust_import

def test_something(request, snapshot):
    # ...testovací logika...
    pass
```

### Další informace
- Kompletní mechanismus a whitelist najdete v komentářích v `tests/conftest.py`.
- Pokud potřebujete rozšířit whitelist nebo auditní logiku, proveďte změnu v `conftest.py` a aktualizujte tuto dokumentaci.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
