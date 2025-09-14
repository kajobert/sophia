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

* **`/sandbox` (Izolované Prostředí)**:
    * **Funkce:** Bezpečný a izolovaný adresář, kde mohou agenti volně vytvářet, upravovat a spouštět soubory a kód, aniž by ovlivnili zbytek systému. Slouží jako testovací pole pro všechny tvůrčí úkoly.

* **`tools/` (Dílna pro Tvůrce)**:
    * **Technologie:** Vlastní implementace
    * **Funkce:** Bude obsahovat nové, klíčové nástroje pro agenty, jako `FileSystemTool` (pro práci se soubory v `/sandbox`) a `CodeExecutorTool` (pro spouštění a testování kódu).

