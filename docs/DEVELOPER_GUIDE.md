# 🛠️ Průvodce pro Vývojáře: Nomad Core

Vítejte, vývojáři! Tento dokument je vaším komplexním průvodcem pro přispívání do projektu. Po rozsáhlém refaktoringu byla zavedena nová, odlehčená a robustní architektura s kódovým označením **Nomad**.

## Filosofie Projektu

Naším cílem je vytvořit **Artificial Mindful Intelligence (AMI)** – entitu, která se nejen učí řešit úkoly, ale přistupuje k nim s určitou kvalitou vědomí. Stavíme most mezi technologií a filosofií. Nová architektura Nomad je pragmatickým krokem k tomuto cíli, zaměřeným na stabilitu, modularitu a interaktivitu.

Pro hlubší vhled do našich principů doporučujeme prostudovat **[🧬 DNA.md](./DNA.md)**.

---

## 1. Architektura a Struktura Projektu

Architektura Nomad je navržena jako modulární systém s centrálním orchestrátorem a odděleným uživatelským rozhraním. Podrobný popis najdete v **[📄 ARCHITECTURE.md](./ARCHITECTURE.md)**.

### Klíčové Komponenty

-   **`tui/app.py` (Textual User Interface):** Hlavní vstupní bod aplikace. Nahrazuje jakýkoli předchozí webový server nebo interaktivní skript. Je zodpovědný za zobrazení a interakci s uživatelem.
-   **`core/orchestrator.py` (JulesOrchestrator):** Srdce agenta. Řídí konverzaci, volá LLM a spravuje nástroje přes MCP klienty.
-   **`mcp_servers/` (Nástroje Agentů):** Sada schopností (nástrojů), které může agent používat. Každý server běží jako samostatný proces a poskytuje skupinu souvisejících nástrojů.
-   **`core/memory_manager.py` (Paměťový Systém):** Využívá SQLite pro ukládání historie konverzací, což umožňuje perzistenci sezení.
-   **`sandbox/` (Izolované Prostředí):** Bezpečný adresář, kde mohou agenti generovat, upravovat a testovat kód, aniž by ohrozili stabilitu hlavní aplikace.

### Technologický Stack

-   **Jazyk:** Python 3.12+
-   **Uživatelské Rozhraní:** [Textual](https://textual.textualize.io/)
-   **LLM:** Google Gemini (konfigurovatelné)
-   **Databáze:** SQLite (pro historii sezení)
-   **Správa Závislostí:** `pip-tools` (`uv` nebo `pip`)
-   **Kontrola Kvality:** `pre-commit` (s `black` a `ruff`)
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
    - Nainstaluje všechny potřebné závislosti z `requirements.txt` pomocí `setup.sh`.
    - Zkontroluje `.env` soubor a pokud v něm chybí `GEMINI_API_KEY`, interaktivně si ho vyžádá.
    - Spustí TUI aplikaci, která se sama postará o inicializaci všech komponent.

---

## 3. Jak Přidat Nový Nástroj

Modularita je klíčová. Přidání nového nástroje je navrženo tak, aby bylo co nejjednodušší.

1.  **Vytvořte nový soubor serveru** v adresáři `mcp_servers/`, například `my_new_tools_server.py`.
2.  **Implementujte v něm logiku serveru**, která bude naslouchat na unikátním portu a poskytovat nástroje přes JSON-RPC. Můžete se inspirovat existujícími servery jako `file_system_server.py`.
3.  **Upravte `core/mcp_client.py`**: Přidejte cestu k vašemu novému skriptu do metody `start_servers`, aby ho orchestrátor automaticky spustil.

**Důležité:** Ujistěte se, že váš nový server správně implementuje `initialize` metodu, která vrací seznam dostupných nástrojů a jejich popisů, aby je orchestrátor mohl nabídnout LLM.

---

## 4. Průvodce Testováním

Kvalitní testy jsou základem stability projektu. Vzhledem k rozsáhlému refaktoringu je stávající testovací sada ve složce `integrace/tests` **zastaralá**.

-   **Spouštění testů:** Prozatím neexistují žádné aktivní testy pro novou architekturu.
-   **Budoucí práce:** Je nezbytné vytvořit novou sadu testů v adresáři `tests/`, která bude pokrývat funkčnost `JulesOrchestrator`, MCP serverů a TUI. Testy by měly být navrženy tak, aby běžely **offline** a mockovaly volání na externí služby (především LLM).

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Pokud zjistíte, že je zastaralý nebo neúplný, založte prosím issue nebo vytvořte pull request s návrhem na jeho aktualizaci. Děkujeme!</sub>
</p>