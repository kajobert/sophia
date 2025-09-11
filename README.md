
# Sophia

Sophia je autonomní agent postavený na CrewAI, zaměřený na bezpečné, auditovatelné a rozšiřitelné zpracování úloh s podporou webového vyhledávání, práce se soubory a duální paměti (krátkodobá i dlouhodobá).

## Rychlý start

1. Vytvoř `.env` v rootu projektu s potřebnými API klíči:
	 ```
	 SERPER_API_KEY="..."
	 GEMINI_API_KEY="..."
	 ```
2. Instalace závislostí:
	 ```bash
	 pip install -r requirements.txt
	 ```
3. Spuštění v interaktivním režimu:
	 ```bash
	 python main.py
	 ```

## Architektura

- **main.py** – Interaktivní smyčka, loguje každý vstup a odpověď do krátkodobé paměti.
- **Paměť**
	- `memory/short_term_memory.py` – krátkodobá (episodická) paměť, loguje události.
	- `memory/long_term_memory.py` – dlouhodobá (vektorová, ChromaDB), připravena k integraci.
- **Nástroje** (core/custom_tools.py):
	- WebSearchTool (Serper)
	- FileWriteTool
	- FileReadTool
	- FileEditTool
- **Agent** (core/agents.py):
	- developer_agent má registrovány všechny nástroje.

## Vývoj a rozšíření

- Kód je PEP8, typované signatury, komentáře a docstringy.
- Pro testování použijte pytest.
- Pro rozšíření paměti viz memory/long_term_memory.py.
- Pro přidání nástrojů editujte core/custom_tools.py a core/agents.py.

## Poznámky

- `.env` nikdy necommitujte.
- Logy a vektorová DB se generují automaticky.
- Projekt je připraven pro týmové předání a další rozvoj.
