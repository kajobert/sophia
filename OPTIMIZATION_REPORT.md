# Zpráva o Optimalizaci a Stabilitě Projektu Sophia

**Datum:** 2025-09-17
**Auditor:** Jules

## 1. Souhrn a Hlavní Zjištění

Tato zpráva navazuje na úvodní audit a zabývá se hloubkovou analýzou implementace a návrhem optimalizací pro zajištění 100% stability projektu před přechodem na Fázi 4 (autonomie).

**Klíčové Zjištění:** Byla identifikována **kritická neshoda** mezi designem jednotlivých agentů a jejich reálnou integrací v hlavním aplikačním cyklu (`main.py`). Zatímco agenti (`EngineerAgent`, `TesterAgent`) jsou správně navrženi pro práci se `SharedContext` objektem, hlavní smyčka tento mechanismus nepoužívá. **To je hlavní příčina nestability a nefunkčnosti plného řetězce spolupráce.**

**Závěr k Úkolu 3.2:** Úkol "Implementace mechanismu pro používání nástrojů" je dokončen pouze z 50 %. Komponenty (agenti a nástroje) existují, ale jejich klíčová integrace a orchestrace chybí.

---

## 2. Plán Oprav a Optimalizací

Následující kroky jsou seřazeny podle priority. Bod 1 je **nezbytné** provést pro zajištění základní funkčnosti. Body 2 a 3 jsou silná doporučení pro dosažení dlouhodobé stability a efektivity.

### Priorita 1: Kritická Oprava Orchestrace Agentů (Architektura)

*   **Problém:** `main.py` nevolá `agent.run_task(context)` a nepředává `SharedContext` mezi agenty. Tím je celý mechanismus předávání dat (plán -> kód -> výsledky testů) nefunkční.
*   **Navrhované Řešení:**
    1.  **Refaktorovat `main.py`:** Kompletně přepsat logiku uvnitř smyčky `while True:`, která zpracovává načtený úkol.
    2.  **Použít Správné Metody:** Místo `task.execute()` na *třídě* agenta je nutné vytvořit **instanci** agenta (`planner = PlannerAgent(llm=get_llm())`) a volat jeho metodu `planner.run_task(context)`.
    3.  **Zajistit Předávání Kontextu:** `SharedContext` objekt musí být sekvenčně předáván mezi agenty. Výstup z jednoho agenta (upravený `context`) se stává vstupem pro dalšího.
    4.  **Zajistit Asynchronní Kompatibilitu:** Všechna volání `crew.kickoff()` uvnitř metod `run_task` jsou blokující. Jelikož `main.py` běží v `asyncio` smyčce, je třeba tato volání spouštět v odděleném vlákně, aby neblokovala hlavní proces.
        ```python
        # Příklad v rámci metody run_task v agentovi
        import asyncio
        # ...
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, crew.kickoff)
        ```

### Priorita 2: Zvýšení Robustnosti Kódu

*   **Problém:** Současné `try...except` bloky v `main.py` jsou příliš obecné. Pouze logují chybu, ale neumožňují systému, aby se z ní zotavil (např. opakováním úkolu po chybě).
*   **Navrhované Řešení:**
    1.  **Implementovat Cyklus Opravy (Retry Loop):** Vytvořit v `main.py` smyčku (např. `for i in range(3)`), která umožní `EngineerAgentovi` 2-3 pokusy na opravu kódu, pokud `TesterAgent` nahlásí chybu. Výsledek testů (`test_results`) by se v takovém případě přidal do kontextu jako zpětná vazba pro další iteraci `EngineerAgenta`.
    2.  **Validovat Výstupy Agentů:** Před voláním dalšího agenta vždy zkontrolovat, zda potřebná data v `context.payload` existují a nejsou prázdná (např. ověřit, že `context.payload.get('code')` není `None` před voláním `TesterAgenta`).

### Priorita 3: Vylepšení Vývojových Procesů

*   **Problém:** Dodržování pravidel z `CODE_OF_CONDUCT.md` a konzistence dokumentace je v současnosti manuální.
*   **Navrhované Řešení:**
    1.  **Zavést Pre-commit Hook:** Použít nástroj `pre-commit` a nakonfigurovat ho tak, aby automaticky spouštěl skript `run_review.py` (a případně další nástroje pro formátování kódu jako `black`) před každým commitem. Tím se automaticky zajistí dodržování klíčových pravidel a zvýší kvalita kódu.
    2.  **Sjednotit Dokumentaci:** Sloučit duplicitní obsah ze souborů `AGENTS.md` a `CODE_OF_CONDUCT.md` do jednoho (`AGENTS.md`) a druhý smazat, aby se předešlo budoucím nekonzistencím.
    3.  **Aktualizovat Roadmapu:** Po implementaci opravy v `main.py` je nutné v souboru `docs/ROADMAP_NEXUS_V1.md` označit úkol **3.2** jako dokončený (`[x]`).

---
## Závěr

Projekt Sophia má velmi pevné a dobře navržené základy v podobě jednotlivých komponent. Kritickým problémem je jejich chybějící propojení. Implementací výše uvedených doporučení, zejména **Priority 1**, se projekt dostane do plně funkčního, stabilního a robustního stavu, připraveného na přechod k Fázi 4.
