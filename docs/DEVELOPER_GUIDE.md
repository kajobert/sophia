# 🛠️ Průvodce pro Vývojáře: Nomad Core

Vítejte, vývojáři! Tento dokument je vaším komplexním průvodcem pro přispívání do projektu. Po rozsáhlém refaktoringu byla zavedena nová, robustní architektura **Manager/Worker**.

## Filosofie Projektu

Naším cílem je vytvořit **Artificial Mindful Intelligence (AMI)** – entitu, která se nejen učí řešit úkoly, ale přistupuje k nim s určitou kvalitou vědomí. Stavíme most mezi technologií a filosofií. Nová architektura je pragmatickým krokem k tomuto cíli, zaměřeným na stabilitu, modularitu a oddělení zodpovědností.

Pro hlubší vhled do našich principů doporučujeme prostudovat **[🧬 DNA.md](./DNA.md)**.

---

## 1. Architektura a Struktura Projektu

Architektura je postavena na modelu **Manager/Worker**. Podrobný popis a diagram najdete v **[📄 ARCHITECTURE.md](./ARCHITECTURE.md)**.

### Klíčové Komponenty

-   **`tui/app.py` (Textual User Interface):** Hlavní vstupní bod aplikace. Zodpovědný za zobrazení a interakci s uživatelem. Předává vstupy `ConversationalManageru`.
-   **`core/conversational_manager.py` (ConversationalManager):** Vrchní řídící vrstva. Vede konverzaci, rozhoduje o dalším kroku (zjistit stav vs. delegovat úkol) a formuluje odpovědi pro uživatele.
-   **`core/orchestrator.py` (WorkerOrchestrator):** "Pracant" systému. Přebírá komplexní úkoly od manažera, používá nástroje k jejich řešení a vrací výsledek.
-   **`mcp_servers/worker/` (Nástroje Workera):** Sada schopností (nástrojů), které může `WorkerOrchestrator` používat. Každý server běží jako samostatný proces a poskytuje skupinu souvisejících nástrojů.
-   **`core/memory_manager.py` (Paměťový Systém):** Využívá SQLite pro ukládání historie konverzací, což umožňuje perzistenci sezení.
-   **`sandbox/` (Izolované Prostředí):** Bezpečný adresář, kde může agent generovat, upravovat a testovat kód, aniž by ohrozil stabilitu hlavní aplikace.

### Technologický Stack

-   **Jazyk:** Python 3.12+
-   **Uživatelské Rozhraní:** [Textual](https://textual.textualize.io/)
-   **LLM:** Google Gemini (konfigurovatelné)
-   **Databáze:** SQLite (pro historii sezení)
-   **Správa Závislostí:** `uv` (z `requirements.in`)
-   **Testování:** `pytest`

---

## 2. Nastavení Lokálního Prostředí

Nastavení je nyní zjednodušeno díky spouštěcímu skriptu.

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

3.  **Spuštění Aplikace:**
    ```bash
    ./start.sh
    ```
    Tento skript automaticky:
    - Nainstaluje všechny potřebné závislosti z `requirements.in` pomocí `uv`.
    - Zkontroluje `.env` soubor a pokud v něm chybí API klíč, interaktivně si ho vyžádá.
    - Spustí TUI aplikaci.

---

## 3. Jak Přidat Nový Nástroj pro Workera

Modularita je klíčová. Přidání nového nástroje pro `WorkerOrchestrator` je snadné a **nevyžaduje úpravu existujícího kódu jádra**.

1.  **Vytvořte logiku nástroje:** Přidejte své funkce do nového souboru v adresáři `tools/`, například `tools/my_new_feature.py`.
2.  **Vytvořte soubor serveru:** V adresáři `mcp_servers/worker/` vytvořte nový soubor končící na `_server.py`, například `my_new_feature_server.py`.
3.  **Implementujte server:** V tomto souboru naimportujte své funkce z `tools/` a vystavte je přes standardní JSON-RPC smyčku. Můžete se inspirovat existujícími servery jako `file_system_server.py`.

`MCPClient` automaticky detekuje a spustí jakýkoliv `*_server.py` soubor v adresáři daného profilu (`worker`). Není potřeba klienta nijak upravovat.

**Důležité:** Ujistěte se, že váš nový server správně implementuje `initialize` metodu, která vrací seznam dostupných nástrojů a jejich popisů (`inspect.getdoc(func)`), aby je `WorkerOrchestrator` mohl nabídnout LLM.

---

## 4. Průvodce Testováním

Kvalitní testy jsou základem stability projektu.

-   **Spouštění testů:** Pro spuštění kompletní testovací sady použijte příkaz:
    ```bash
    PYTHONPATH=. .venv/bin/python -m pytest
    ```
    Všechny testy musí projít před odesláním změn.
-   **Stav pokrytí:** Testovací sada pokrývá klíčové funkce, včetně I/O operací se soubory, plánování úkolů a parsování odpovědí z LLM. Je třeba ji dále rozšiřovat s přidáváním nových funkcí.
-   **Filosofie testování:** Testy by měly být co nejvíce izolované a v ideálním případě by měly mockovat volání na externí služby (především LLM), aby byla zajištěna jejich rychlost a spolehlivost.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>