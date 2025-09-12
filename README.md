# Sophia

Sophia je autonomní agent postavený na CrewAI, zaměřený na bezpečné, auditovatelné a rozšiřitelné zpracování úloh s podporou webového vyhledávání, práce se soubory a duální paměti (krátkodobá i dlouhodobá). Po každé interakci probíhá automaticky proces "snění" (konsolidace paměti), kdy specializovaný agent ukládá klíčové poznatky do dlouhodobé paměti.


## Instalace a první spuštění

1. **Klonujte repozitář a spusťte instalační skript:**
	```bash
	git clone ...
	cd sophia
	bash install.sh
	```

2. **Doplňte API klíče do `.env` (vytvoří se šablona):**
	- `GOOGLE_API_KEY` – pro webové vyhledávání (Serper)
	- `SERPER_API_KEY` – pro Serper API (volitelné)
	- `GEMINI_API_KEY` – pro Gemini LLM (volitelné)

3. **Spusťte Sophiu:**
	```bash
	source .venv/bin/activate
	python main.py
	```

4. **Základní práce:**
	- Pište přirozené dotazy, Sophia rozhoduje, zda jde o znalost (uloží do LTM) nebo poznámku (uloží do souboru).
	- Všechny znalosti a fakta jsou ukládány do dlouhodobé paměti (ChromaDB).
	- Po každé odpovědi probíhá konsolidace paměti ("snění").

## Rychlý start (alternativa)

Pokud nechcete použít install.sh:
1. Vytvořte a aktivujte venv, nainstalujte závislosti z requirements.txt, vytvořte .env a spusťte main.py ručně.

## Architektura

- **main.py** – Interaktivní smyčka, loguje každý vstup a odpověď do krátkodobé paměti. Po každé odpovědi se automaticky spouští proces konsolidace paměti ("snění").
- **Paměť**
	- `memory/short_term_memory.py` – krátkodobá (episodická) paměť, loguje události.
	- `memory/long_term_memory.py` – dlouhodobá (vektorová, ChromaDB), využívána memory agentem pro ukládání znalostí.
	- `core/memory_agent.py` – specializovaný agent pro konsolidaci paměti.
	- `core/memory_tasks.py` – úkol pro konsolidaci paměti.
- **Nástroje** (core/custom_tools.py):
	- DecisionTool (rozhoduje, zda prompt patří do LTM nebo do souboru, znalosti ukládá do LTM)
	- LtmWriteTool (zápis znalostí do dlouhodobé paměti)
- **Agent** (core/agents.py):
	- developer_agent má registrovány pouze bezpečné BaseTool nástroje.

## Vývoj a rozšíření

- Kód je PEP8, typované signatury, komentáře a docstringy.
- Pro testování použijte pytest.
- Po každé interakci probíhá konsolidace paměti: memory agent analyzuje krátkodobou paměť a ukládá klíčové poznatky do dlouhodobé (ChromaDB).
- Pro přidání nástrojů editujte core/custom_tools.py a core/agents.py.


## Další poznámky

- `.env` nikdy necommitujte.
- Logy a vektorová DB se generují automaticky.
- Projekt je připraven pro týmové předání a další rozvoj. Kognitivní cyklus (interakce + snění) je plně funkční.

Toto je čistá verze pro GitHub. Sophia.