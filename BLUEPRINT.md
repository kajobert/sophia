# Finální Architektonický Plán pro Nomáda 2.0

Tento dokument definuje finální, zjednodušenou a robustní architekturu pro projekt Nomád, postavenou na poučeních z předchozích iterací.

## 1. Hlavní Cíl

Vytvořit skutečně autonomního AI softwarového inženýra schopného samostatně plánovat, provádět a reflektovat komplexní vývojářské úkoly v rámci daného projektu.

## 2. Klíčové Principy Návrhu

-   **Jednoduchost (Princip Jednoho Mozku):** Veškerá inteligence a rozhodování jsou soustředěny v jediném centrálním orchestrátoru. Odstraňujeme všechny nadbytečné manažerské vrstvy, které způsobovaly fragmentaci kontextu.
-   **Stavovost (Princip Nepřerušitelné Paměti):** Architektura je explicitně navržena jako stavový stroj. Agent si je vždy vědom toho, v jaké fázi práce se nachází, což mu umožňuje plynule navázat na práci i po přerušení nebo restartu.
-   **Robustnost (Princip Jasných Datových Toků):** Datové a řídící toky jsou co nejjednodušší a nejpřímější. Minimalizujeme počet "předávání" zodpovědnosti, abychom předešli chybám a ztrátě informací.

## 3. Cílová Architektura: "Jeden Mozek - Stavový Stroj"

Základem nové architektury je jediná řídící třída a sada jasně definovaných stavů, kterými prochází.

### 3.1. Centrální Orchestrátor: `NomadOrchestrator`

-   **Soubor:** `core/orchestrator.py`
-   **Role:** Toto je jediný "mozek" systému. Je zodpovědný za celý životní cyklus úkolu:
    1.  Přijímá a analyzuje uživatelský požadavek.
    2.  Vytváří podrobný, více-krokový plán.
    3.  Iterativně provádí každý krok plánu (volá nástroje).
    4.  Zpracovává výsledky nástrojů a řeší chyby.
    5.  Udržuje a aktualizuje svůj vnitřní stav.
    6.  Po dokončení úkolu provádí sebereflexi a ukládá poučení.
    7.  Komunikuje s uživatelem.

### 3.2. Stavový Stroj (State Machine)

`NomadOrchestrator` se vždy nachází v jednom z následujících stavů. Přechod mezi stavy je explicitní a logovaný.

-   `AWAITING_USER_INPUT`:
    - **Popis:** Výchozí stav. Orchestrátor je nečinný a čeká na pokyn od uživatele.
    - **Přechod:** Po obdržení vstupu přechází do stavu `PLANNING`.

-   `PLANNING`:
    - **Popis:** Orchestrátor obdržel komplexní úkol. Pomocí LLM a dedikovaného promptu analyzuje zadání a generuje podrobný, proveditelný plán (seznam kroků).
    - **Přechod:** Po úspěšném vytvoření plánu přechází do stavu `EXECUTING_STEP`.

-   `EXECUTING_STEP`:
    - **Popis:** Orchestrátor vybere další nedokončený krok z plánu. Pomocí LLM rozhodne, který nástroj je pro tento krok nejvhodnější, a připraví jeho volání.
    - **Přechod:** Po rozhodnutí o volání nástroje přechází do stavu `AWAITING_TOOL_RESULT`.

-   `AWAITING_TOOL_RESULT`:
    - **Popis:** Orchestrátor zavolal nástroj (přes `MCPClient`) a asynchronně čeká na jeho výsledek.
    - **Přechod:** Po obdržení výsledku (ať už úspěšného, nebo chybového) přechází zpět do `EXECUTING_STEP`, aby mohl pokračovat dalším krokem nebo řešit chybu.

-   `REFLECTION`:
    - **Popis:** Všechny kroky v plánu byly dokončeny. Orchestrátor analyzuje celou historii své práce (myšlenky, volání nástrojů, výsledky) a generuje z ní klíčové "poučení" (`learning`). Toto poučení uloží do dlouhodobé paměti.
    - **Přechod:** Po uložení poučení přechází do stavu `RESPONDING`.

-   `RESPONDING`:
    - **Popis:** Orchestrátor formuluje finální, souhrnnou odpověď pro uživatele, která popisuje výsledek práce.
    - **Přechod:** Po odeslání odpovědi přechází zpět do výchozího stavu `AWAITING_USER_INPUT`.

### 3.3. Perzistence Stavu

Aby agent přežil restart, jeho klíčový stav bude po každé významné operaci (změně stavu, dokončení kroku) perzistován.

-   **Mechanismus:** Jednoduchý soubor `memory/session.json`.
-   **Obsah:** JSON objekt obsahující:
    -   `current_state`: Aktuální stav ze stavového stroje (např. `EXECUTING_STEP`).
    -   `session_id`: Unikátní ID aktuální session.
    -   `mission_prompt`: Původní zadání od uživatele.
    -   `plan`: Kompletní plán (seznam kroků) s označením, které jsou již hotové.
    -   `history`: Kompletní historie konverzace a volání nástrojů.

## 4. Cílová Adresářová Struktura a Klíčové Soubory

Struktura bude zjednodušena a zpřehledněna.

```
.
├── core/
│   ├── orchestrator.py      # Definuje NomadOrchestrator a jeho stavový stroj.
│   ├── mcp_client.py        # Klient pro komunikaci s nástrojovými servery (zůstává).
│   ├── llm_manager.py       # Správa a konfigurace LLM (zůstává).
│   ├── long_term_memory.py  # Správa vektorové databáze pro poučení (zůstává).
│   └── prompt_builder.py    # Logika pro sestavování promptů (zůstává).
│
├── tools/                  # Adresář pro všechny dostupné nástroje (jednoduché Python funkce).
│   ├── file_system_tools.py
│   └── ...
│
├── mcp_servers/            # Servery, které vystavují nástroje přes MCP.
│   └── tool_server.py      # Jeden generický server, který umí načíst a obsloužit všechny nástroje z `tools/`.
│
├── memory/
│   ├── session.json        # Soubor pro perzistenci stavu orchestrátoru.
│   └── db/                 # Adresář pro ChromaDB databázi.
│
├── prompts/                # Adresář pro všechny prompt templaty.
│   ├── planning_prompt.txt
│   ├── execution_prompt.txt
│   └── reflection_prompt.txt
│
├── tui/                    # Textové uživatelské rozhraní (zůstává).
│   └── app.py
│
├── config/
│   └── config.yaml         # Hlavní konfigurační soubor.
│
├── tests/                  # Testy.
│
└── main.py                 # Hlavní vstupní bod aplikace.
```

Tento blueprint představuje radikální zjednodušení, které eliminuje hlavní zdroje chyb a ztráty kontextu. Vytváří solidní, udržitelný a škálovatelný základ pro budoucí vývoj Nomáda.