# Detailní Plán Refaktoringu na Hierarchickou Kognitivní Architekturu

> **NOTE (2025-09-24):** Tento refactoring byl úspěšně implementován a sloučen do `master` větve. Dokument nyní slouží primárně jako historický záznam plánu a doporučení. Aktuální architektura je popsána v `docs/COGNITIVE_ARCHITECTURE.md`.

Tento dokument slouží jako detailní, krok-za-krokem plán pro refaktoring projektu Sophia ze stávajícího stavu na novou Hierarchickou Kognitivní Architekturu (HKA).

**Cílový Stav:** Funkční MVP nové architektury, které lze plně ovládat a testovat přes terminál (`interactive_session.py`). Klíčovou schopností tohoto MVP musí být **autonomní úprava vlastního kódu**.

---

## Fáze 1: Základy a Odstranění Závislostí

**Cíl:** Připravit kódovou základnu, odstranit nepotřebné závislosti a vytvořit stabilní bod pro další vývoj.

1.  **Odstranit `crewai` z `agents/planner_agent.py`:**
    *   **Akce:** Přepsat `PlannerAgent` tak, aby používal přímé volání LLM (`self.llm.generate_text`).
    *   **Zachovat:** Logiku pro generování JSON, parsování a opakované pokusy (retry logic).
2.  **Aktualizovat Testy pro `PlannerAgent`:**
    *   **Akce:** Přepsat `tests/test_planner_agent.py`, aby testoval novou, framework-free implementaci.
    *   **Ověřit:** Schopnost generovat platný JSON plán, správně reagovat na neplatný JSON a dodržet `MAX_RETRIES`.
3.  **Vyčistit Závislosti:**
    *   **Akce:** Odstranit `crewai` a `crewai-tools` z `requirements.in`.
    *   **Akce:** Přidat `marko` pro parsování Markdownu.
    *   **Ověřit:** Spustit `uv pip install -r requirements.in` a následně celou testovací sadu, abychom se ujistili, že systém je po této změně stabilní.

## Fáze 2: Implementace a Testování Kognitivních Vrstev

**Cíl:** Vytvořit a otestovat jednotlivé komponenty nové architektury v izolaci.

1.  **Vytvořit Strukturu Souborů:**
    *   **Akce:** Vytvořit `core/cognitive_layers.py` a `core/memory_systems.py`.
2.  **Implementovat `ReptilianBrain`:**
    *   **Akce:** V `core/cognitive_layers.py` vytvořit třídu `ReptilianBrain`.
    *   **Akce:** Implementovat metodu `_load_dna` s použitím knihovny `marko` pro robustní parsování `docs/DNA.md`.
    *   **Akce:** Implementovat metodu `_call_nano_model` pro volání lokálního LLM (Ollama).
    *   **Akce:** Implementovat hlavní metodu `process_input`, která provede bezpečnostní kontrolu a základní strukturování vstupu.
3.  **Implementovat Paměťové Systémy:**
    *   **Akce:** V `core/memory_systems.py` implementovat třídu `ShortTermMemory` pro práci s Redis.
    *   **Akce:** V `core/memory_systems.py` implementovat třídu `LongTermMemory` pro práci s PostgreSQL/pgvector (s placeholder logikou pro SQL dotazy).
4.  **Implementovat `MammalianBrain`:**
    *   **Akce:** V `core/cognitive_layers.py` vytvořit třídu `MammalianBrain`, která bude přijímat `LongTermMemory` jako závislost.
    *   **Akce:** Implementovat `process_input`, která obohatí data o kontext z dlouhodobé paměti.
5.  **Refaktorovat `Orchestrator` na `Neocortex`:**
    *   **Akce:** Přejmenovat `core/orchestrator.py` na `core/neocortex.py`.
    *   **Akce:** Přejmenovat třídu `Orchestrator` na `Neocortex`.
    *   **Akce:** Upravit `__init__`, aby přijímal `ShortTermMemory` jako závislost.
    *   **Akce:** Refaktorovat `execute_plan` na `process_input` a `_execute_plan_loop`, které budou pracovat se stavem uloženým v `ShortTermMemory`.
    *   **Opravit:** Chybnou logiku v cyklu pro opravu plánů, aby se neopakoval celý plán.
6.  **Napsat Jednotkové Testy:**
    *   **Akce:** Vytvořit nové testovací soubory (`tests/test_reptilian_brain.py`, `tests/test_mammalian_brain.py`) a upravit `tests/test_neocortex_cycle.py`.
    *   **Ověřit:** Každá vrstva musí být testována v izolaci s mockovanými závislostmi.

## Fáze 3: Integrace, Zprovoznění a End-to-End Testování

**Cíl:** Propojit všechny nové komponenty do funkčního celku a ověřit klíčovou schopnost autonomie.

1.  **Aktualizovat Vstupní Body:**
    *   **Akce:** Upravit `main.py` a `interactive_session.py`, aby správně inicializovaly a propojovaly všechny tři kognitivní vrstvy a jejich paměťové systémy.
    *   **Akce:** Upravit hlavní smyčku v `interactive_session.py` tak, aby data procházela celým kognitivním řetězcem: `Vstup -> ReptilianBrain -> MammalianBrain -> Neocortex -> Výstup`.
2.  **Opravit API Testy:**
    *   **Akce:** Upravit `tests/web_api/test_task_endpoints.py`, aby správně mockoval `Neocortex` a testy procházely.
3.  **Provést Autonomní Test:**
    *   **Akce:** Spustit `interactive_session.py` a zadat finální testovací úkol: `"Sophia, analyzuj a vylepši prompt pro strukturování dat ('structuring_prompt') ve své třídě ReptilianBrain v souboru core/cognitive_layers.py."`
    *   **Ověřit:** Manuálně zkontrolovat, zda Sophia dokázala úspěšně přečíst, analyzovat a upravit svůj vlastní zdrojový kód.
4.  **Závěrečná Dokumentace:**
    *   **Akce:** Po úspěšném dokončení všech kroků vytvořit záznam o provedených změnách v `docs/KNOWLEDGE_BASE.md`.

---

**Technologická Doporučení:**
*   **Lokální LLM:** `Ollama` s modelem `phi3:mini` nebo podobným.
*   **Krátkodobá Paměť:** `Redis`.
*   **Dlouhodobá Paměť:** `PostgreSQL` s rozšířením `pgvector`.
*   **Parsování Markdownu:** `marko`.
*   **Interní API:** `FastAPI` (pro budoucí komunikaci mezi vrstvami, pokud by byly odděleny do samostatných služeb).
