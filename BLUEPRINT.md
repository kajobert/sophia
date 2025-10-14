# Finální Architektonický Plán pro Nomáda 2.0

Tento dokument definuje finální, zjednodušenou a robustní architekturu pro projekt Nomád, založenou na ponaučeních z předchozích neúspěšných iterací.

## 1. Hlavní Cíl

Nomád je **autonomní AI softwarový inženýr** schopný samostatně řešit komplexní úkoly, učit se z chyb a efektivně komunikovat s uživatelem.

## 2. Klíčové Principy Návrhu

1.  **Jednoduchost (Princip jednoho mozku):** Veškerá inteligence a rozhodování jsou soustředěny v jediném centrálním orchestrátoru. Odstraňujeme všechny nadbytečné vrstvy (`MissionManager`, `ConversationalManager`).
2.  **Stavovost (Princip paměti):** Architektura je postavena na explicitním stavovém stroji. Agent si je vždy vědom toho, v jakém stavu se nachází, což zabraňuje "amnézii" a umožňuje plynulé navázání na práci.
3.  **Robustnost (Princip jasných toků):** Datové toky jsou jednoduché a centralizované. Veškerý relevantní stav (plán, historie, výsledky) je držen na jednom místě, což minimalizuje riziko chyb a ztráty kontextu.

## 3. Cílová Architektura: "Jeden Mozek - Stavový Stroj"

### 3.1. Centrální Orchestrátor: `NomadOrchestrator`

*   **Soubor:** `core/orchestrator.py`
*   **Role:** Je to jediná řídící třída ("mozek"). Zodpovídá za celý životní cyklus úkolu:
    *   Přijímá vstup od uživatele.
    *   Spravuje svůj stav pomocí `StateManager`.
    *   Vytváří a spravuje plány (`PlanManager`).
    *   Volá nástroje (`MCPClient`).
    *   Reflektuje svůj postup (`ReflectionEngine`).
    *   Formuluje odpovědi pro uživatele.

### 3.2. Stavový Stroj (State Machine)

Orchestrátor funguje jako stavový stroj. Toto je srdce celé architektury.

*   **Soubor:** `core/state_manager.py`
*   **Klíčové Stavy:**
    *   `AWAITING_USER_INPUT`: Agent je nečinný a čeká na pokyn od uživatele. Výchozí stav.
    *   `PLANNING`: Agent obdržel komplexní úkol. Analyzuje jej a generuje strukturovaný plán (seznam kroků).
    *   `EXECUTING_STEP`: Agent bere další krok z plánu a připravuje volání nástroje.
    *   `AWAITING_TOOL_RESULT`: Agent zavolal nástroj a čeká na jeho výsledek.
    *   `REFLECTION`: Po dokončení úkolu (nebo při chybě) agent analyzuje svůj postup, identifikuje poučení a ukládá je do dlouhodobé paměti.
    *   `RESPONDING`: Agent formuluje finální odpověď nebo stavovou aktualizaci pro uživatele.

### 3.3. Perzistence Stavu

*   **Mechanismus:** Po každé významné akci (změna stavu, dokončení kroku plánu) si `NomadOrchestrator` uloží svůj kompletní stav do jediného JSON souboru.
*   **Soubor:** `memory/session.json`
*   **Obsah souboru:**
    ```json
    {
      "session_id": "20251014_100000",
      "current_state": "EXECUTING_STEP",
      "plan": {
        "goal": "Refactor the authentication module.",
        "steps": [...],
        "current_step": 3
      },
      "history": [...]
    }
    ```
*   **Cíl:** Pokud se aplikace restartuje, orchestrátor si načte tento soubor a může okamžitě pokračovat v práci přesně tam, kde skončil.

## 4. Adresářová Struktura a Klíčové Soubory

```
.
├── core/
│   ├── orchestrator.py       # Hlavní třída NomadOrchestrator
│   ├── state_manager.py      # Třída pro správu stavového stroje
│   ├── mcp_client.py         # Klient pro volání nástrojů (beze změny)
│   └── rich_printer.py       # Utilita pro logování (beze změny)
├── tools/
│   └── ...                   # Adresář s dostupnými nástroji (beze změny)
├── memory/
│   └── session.json          # Soubor pro uložení stavu sezení
├── tui/
│   └── app.py                # Hlavní soubor pro Textual UI, bude integrován s orchestrátorem
└── tests/
    └── ...                   # Testy pro všechny komponenty, včetně nového orchestrátoru
```

Tato architektura je navržena tak, aby byla maximálně jednoduchá, transparentní a robustní, a aby se vyhnula všem chybám identifikovaným v `LESSONS_LEARNED.md`.