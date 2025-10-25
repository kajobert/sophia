# Znovu Použitelný Kód a Koncepty

Tento dokument obsahuje pečlivě vybraný seznam úryvků kódu, návrhových vzorů a konceptů z archivů, které jsou přímo aplikovatelné na nové MVP.

---

## 1. Logika Jádra (Kernel) (z `nomad-archived`)

Stavový automat `NomadOrchestratorV2` poskytuje produkčně ověřený návrh pro `ConsciousnessLoop` v `core/kernel.py`.

**Koncept: Proaktivní Stavový Automat**

Namísto pevného, předem definovaného plánu by hlavní smyčka měla být jednoduchý, nepřetržitý cyklus, který v každém kroku rozhoduje o jediném nejlepším dalším kroku.

**Úryvek Kódu: Smyčka Stavového Automatu**

Toto je hlavní prováděcí smyčka. Může být adaptována tak, aby volala `PluginManager` namísto pevně zakódovaného `MCPClient`.

```python
# Inspired by NomadOrchestratorV2.execute_mission

class Kernel:
    # ... (nastavení)

    async def consciousness_loop(self):
        self.current_state = "THINKING" # Nebo nějaký počáteční stav

        while self.current_state != "MISSION_COMPLETE":
            if self.current_state == "THINKING":
                # 1. Použij plugin pro myšlení/LLM k rozhodnutí o další akci
                # 2. Tato akce může být volání nástroje nebo mission_complete
                # 3. Aktualizuj stav na EXECUTING_PLUGIN
                pass
            elif self.current_state == "EXECUTING_PLUGIN":
                # 1. Použij PluginManager k vykonání zvoleného pluginu
                # 2. Při úspěchu přidej výsledek do kontextu a vrať se do stavu THINKING
                # 3. Při neúspěchu přidej chybu a přejdi do stavu HANDLING_ERROR
                pass
            elif self.current_state == "HANDLING_ERROR":
                # 1. Použij plugin pro myšlení/LLM k rozhodnutí o nápravné akci
                # 2. Aktualizuj stav na EXECUTING_PLUGIN s novou akcí
                pass

            await asyncio.sleep(0.1)
```

---

## 2. Interakce s LLM a Tvorba Promptů (z `nomad-archived`)

Metody `_build_prompt` a `_parse_llm_response` jsou vysoce znovupoužitelné pro jakýkoli plugin, který potřebuje interagovat s LLM (např. `tool_llm.py`).

**Koncept: Strukturované Prompty**

Robustní prompt by měl vždy obsahovat stejné klíčové sekce: hlavní cíl, dostupné nástroje, historii předchozích akcí a jasný konečný pokyn.

**Úryvek Kódu: Sestavení Promptu**

```python
# Inspired by NomadOrchestratorV2._build_prompt

def build_system_prompt(goal: str, history: list, available_tools: str) -> str:
    history_str = "\n".join([f"**{item['role'].upper()}**:\n{item['content']}" for item in history])
    instruction = "Analyze the goal and history. What is the single best next step (as a tool call) to achieve the goal?"

    return f"""
You are an autonomous AI assistant. Your goal is to solve the user's request by calling tools.

**MISSION GOAL:** {goal}

**AVAILABLE TOOLS:**
{available_tools}

**MISSION HISTORY:**
{history_str}

**INSTRUCTION:**
{instruction}

You must respond with a single JSON object representing the tool call.
"""
```

**Koncept: Robustní Parsování JSON**

LLM modely nevracejí vždy dokonalý JSON. Obalení odpovědi regulárním výrazem pro extrakci JSON bloku před parsováním je odolný vzor.

**Úryvek Kódu: Parsování Odpovědi od LLM**

```python
# Inspired by NomadOrchestratorV2._parse_llm_response
import re
import json

def parse_llm_json_response(llm_response: str) -> dict:
    try:
        match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        return {"error": "No JSON object found in response"}
    except json.JSONDecodeError:
        return {"error": f"Failed to decode JSON: {llm_response}"}

```

---

## 3. Rozhraní Paměťových Systémů (z `sophia-archived`)

Soubor `memory_systems.py` poskytuje čisté a jednoduché API pro krátkodobou i dlouhodobou paměť, které může být přímo použito jako kontrakt pro naše nové paměťové pluginy.

**Koncept: Abstraktní API pro Paměť**

Implementační detaily backendu paměti (slovník v paměti, SQLite, ChromaDB) by měly být skryty za jednoduchým a konzistentním rozhraním.

**Úryvek Kódu: API Krátkodobé Paměti**

Toto rozhraní je ideální pro plugin `memory_sqlite`.

```python
# Inspired by ShortTermMemory class

class ShortTermMemoryPlugin:
    def get(self, session_id: str) -> dict:
        # ... implementace ...
        pass

    def set(self, session_id: str, data: dict) -> None:
        # ... implementace ...
        pass

    def update(self, session_id: str, partial_data: dict) -> None:
        # ... implementace ...
        pass

    def clear(self, session_id: str) -> None:
        # ... implementace ...
        pass
```

**Úryvek Kódu: API Dlouhodobé Paměti**

Toto rozhraní je perfektním výchozím bodem pro plugin `memory_chroma`.

```python
# Inspired by LongTermMemory class

class LongTermMemoryPlugin:
    def add_record(self, text: str, metadata: dict) -> str:
        # ... implementace pro vytvoření embeddingu a uložení ...
        pass

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        # ... implementace pro vytvoření query embeddingu a vyhledání ...
        pass
```

---

## 4. Autonomní Konsolidace Paměti (z `sophia-old-archived`)

Koncept "snění" je silná myšlenka pro inteligentnější a spravovanou dlouhodobou paměť agenta.

**Koncept: "Snění" pro Správu Znalostí**

Po dokončení uživatelské session se spustí proces na pozadí nebo dedikovaný agent, který analyzuje krátkodobou paměť session (přepis konverzace). Identifikuje klíčová fakta, poznatky nebo úspěšná řešení a uloží destilovanou, kanonickou verzi do dlouhodobého sémantického paměťového úložiště. Tím se zabrání zahlcení dlouhodobé paměti konverzačním šumem.

**Nápad na Implementaci na Vysoké Úrovni:**

Toto by byla funkce pro budoucí verzi pluginu `memory_chroma`.

```python
# Koncept na vysoké úrovni pro funkci "snění"

class LongTermMemoryPlugin:
    # ... (add_record, search)

    def consolidate_session(self, session_history: list[dict]):
        # 1. Vytvoř prompt pro LLM, který ho požádá o extrakci klíčových poznatků
        #    z historie konverzace.
        prompt = f"Analyze the following conversation and extract any key facts, learned lessons, or important information that should be saved for the future. Conversation:\n{session_history}"

        # 2. Zavolej LLM.
        # insights = llm.generate(prompt)

        # 3. Zpracuj poznatky a ulož je do vektorového úložiště.
        # for insight in insights:
        #     self.add_record(insight, {"source_session": session_id})
        pass
```
