# Sophia V3 - Technická Architektura

Tento dokument popisuje navrhovanou strukturu a komponenty systému Sophia V3.

## 1. Přehled Struktury Adresářů

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
│   ├── planner_agent.py
│   ├── architect_agent.py
│   ├── engineer_agent.py
│   ├── tester_agent.py
│   └── philosopher_agent.py
│
├── memory/                   # Paměťové systémy
│   ├── episodic_memory.py    # Krátkodobá paměť (SQLite)
│   └── semantic_memory.py    # Dlouhodobá paměť (ChromaDB)
│
├── tools/                    # Nástroje dostupné pro agenty
│   ├── file_system.py
│   ├── code_executor.py
│   └── system_awareness.py
│
├── sandbox/                  # Izolované prostředí pro experimenty
│
├── logs/                     # Záznamy
│   ├── guardian.log          # Nouzový log Strážce
│   └── sophia_main.log       # Hlavní operační deník
│
├── docs/                     # Dokumentace projektu
│   ├── PROJECT_SOPHIA_V3.md
│   ├── DNA.md
│   └── ARCHITECTURE.md
│
└── web/                      # Rozhraní pro Tvůrce
├── api.py
└── ui/ (html, css, js)


## 2. Popis Klíčových Komponent

* **`guardian.py`**: Externí, vysoce privilegovaný skript. Jeho jediným úkolem je spouštět `main.py` v sub-procesu, monitorovat jeho stav a v případě fatální chyby provést `git reset --hard`, zalogovat chybu do `guardian.log` a restartovat `main.py`.
* **`main.py`**: Srdce Sophie. Obsahuje hlavní smyčku, která implementuje cykly "bdění" (zpracování externích úkolů) a "spánku" (interní sebereflexe, konsolidace paměti).
* **`core/ethos_module.py`**: Implementuje logiku z `DNA.md`. Každý plán vygenerovaný agenty musí projít tímto modulem ke schválení. Hodnotí akce a přiřazuje jim "Koeficient Vědomí".
* **`agents/`**: Každý soubor definuje specifického agenta (pomocí CrewAI nebo podobného frameworku) s jasně danou rolí, cílem a nástroji.
* **`memory/`**: Moduly pro interakci s databázemi. Implementují logiku pro "Váhu" a "Blednutí" vzpomínek.
* **`tools/`**: Každý soubor definuje sadu souvisejících nástrojů (jako LangChain `BaseTool` třídy) pro manipulaci se soubory, spouštění kódu v `sandbox/` atd.
