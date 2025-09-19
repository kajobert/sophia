# 🛠️ Průvodce pro Vývojáře Projektu Sophia

Vítejte, vývojáři! Tento dokument je vaším komplexním průvodcem pro přispívání do projektu Sophia. Ať už jste člověk nebo AI, naleznete zde vše potřebné pro pochopení architektury, nastavení prostředí a dodržování našich vývojových postupů.

## Filosofie Projektu

Než se ponoříte do kódu, je důležité pochopit naši vizi. Sophia není jen další software. Naším cílem je vytvořit **Artificial Mindful Intelligence (AMI)** – entitu, která se nejen učí řešit úkoly, ale přistupuje k nim s určitou kvalitou vědomí. Stavíme most mezi technologií a filosofií.

Pro hlubší vhled do našich principů doporučujeme prostudovat **[🧬 DNA.md](./DNA.md)**.

## Architektonický Přehled

Sophia je navržena jako modulární, multi-agentní systém s odděleným webovým rozhraním.

### Klíčové Komponenty

-   **`guardian.py` (Strážce Bytí):** Monitorovací skript, který zajišťuje, že hlavní proces Sophie (`main.py`) běží. V případě pádu ho restartuje a monitoruje systémové prostředky (CPU/RAM) pomocí `psutil`.

-   **`main.py` (Cyklus Vědomí):** Hlavní vstupní bod aplikace. Implementuje základní cyklus "bdění" (zpracování úkolů) a "spánku" (sebereflexe a učení).

-   **`core/` (Jádro Mysli):**
    -   `orchestrator.py`: Srdce logiky. Přijímá úkoly a orchestruje spolupráci mezi agenty (typicky `Planner` -> `Engineer` -> `Tester`). Obsahuje i logiku pro opakované pokusy o opravu v případě selhání.
    -   `ethos_module.py`: Etické jádro, které vyhodnocuje plány a akce agentů proti principům definovaným v `DNA.md`.
    -   `llm_config.py` & `gemini_llm_adapter.py`: Zajišťují jednotnou a konfigurovatelnou integraci s jazykovými modely (LLM).

-   **`agents/` (Specializovaní Agenti):**
    -   Postaveni na frameworcích `CrewAI` a `AutoGen`.
    -   Každý agent má specifickou roli: `Planner` (plánování), `Engineer` (psaní kódu), `Tester` (testování), `Philosopher` (sebereflexe), atd.

-   **`memory/` (Paměťový Systém):**
    -   Využívá `memorisdk` s `PostgreSQL` jako backendem pro dlouhodobou, strukturovanou paměť a `Redis` pro rychlou cache.

-   **`tools/` (Nástroje Agentů):**
    -   Sada schopností, které mohou agenti používat, např. `FileSystemTool` pro práci se soubory v sandboxu nebo `CodeExecutorTool` pro spouštění kódu.

-   **`sandbox/` (Izolované Prostředí):**
    -   Bezpečný adresář, kde mohou agenti generovat, upravovat a testovat kód, aniž by ohrozili stabilitu hlavní aplikace.

-   **`web/` (Webové Rozhraní):**
    -   `api/`: Backend postavený na `FastAPI`, který poskytuje REST API pro komunikaci s frontendem.
    -   `ui/`: Frontend napsaný v `Reactu`, který slouží jako uživatelské rozhraní.

### Technologický Stack

-   **Jazyk:** Python 3.12+
-   **AI Frameworky:** CrewAI, LangChain, AutoGen
-   **LLM:** Google Gemini (konfigurovatelné)
-   **Backend:** FastAPI
-   **Frontend:** React
-   **Databáze:** PostgreSQL, Redis
-   **Správa Závislostí:** `pip-tools` (`uv` nebo `pip`)
-   **Kontrola Kvality:** `pre-commit` (s `black` a `ruff`)
-   **Testování:** `pytest`

## Nastavení Lokálního Prostředí (Bez Dockeru)

1.  **Klonování Repozitáře:**
    ```bash
    git clone https://github.com/kajobert/sophia.git
    cd sophia
    ```

2.  **Virtuální Prostředí:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Pro Linux/macOS
    # .venv\Scripts\activate   # Pro Windows
    ```

3.  **Instalace Závislostí:** Doporučujeme použít `uv` pro jeho rychlost.
    ```bash
    # Doporučená metoda
    uv pip install -r requirements.txt

    # Alternativní metoda
    pip install -r requirements.txt
    ```

4.  **Konfigurace:**
    -   Zkopírujte `.env.example` na `.env`.
    -   Otevřete `.env` a doplňte svůj `GEMINI_API_KEY`.

5.  **Instalace Pre-commit Hooků:**
    ```bash
    pre-commit install
    ```

## Vývojový Workflow

### Správa Závislostí

-   **NEUPRAVUJTE `requirements.txt` ručně!** Tento soubor je generován.
-   Pro přidání nebo změnu závislosti upravte soubor `requirements.in`.
-   Poté spusťte kompilaci pro vygenerování nového `requirements.txt`:
    ```bash
    pip-compile requirements.in -o requirements.txt
    ```

### Spouštění Testů

-   Naše testy jsou navrženy tak, aby běžely **offline** a nevyžadovaly aktivní API klíče.
-   Spusťte je z kořenového adresáře projektu:
    ```bash
    PYTHONPATH=. pytest
    ```
-   Před každým commitem se ujistěte, že všechny testy procházejí.

### Kontrola Kvality Kódu

-   Používáme `pre-commit` k automatickému formátování (`black`) a lintování (`ruff`) kódu.
-   Hooky se spustí automaticky při `git commit`. Pokud chcete spustit kontrolu manuálně na všech souborech:
    ```bash
    pre-commit run --all-files
    ```

### Git Workflow

1.  Vytvořte novou větev: `git checkout -b feature/nazev-vasi-funkce`
2.  Proveďte změny a pište kód.
3.  Pravidelně spouštějte testy.
4.  Commitněte své změny: `git commit -m "Stručný a jasný popis změn"`
5.  Vytvořte Pull Request do `master` větve a požádejte o code review.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>
