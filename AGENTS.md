## Sophia – Agent a nástroje

### Agent
- **developer_agent** (core/agents.py)
	- Role: Autonomous Software Developer
	- Cíl: Plnit úkoly pomocí dostupných nástrojů (web search, file read/write/edit)
	- LLM: gemini/gemini-2.5-flash
	- Delegace: zakázána (single-agent)

### Nástroje
- **WebSearchTool** – vyhledávání na webu (Serper)
- **FileWriteTool** – zápis do souboru (přepis)
- **FileReadTool** – čtení souboru
- **FileEditTool** – append do souboru (s ochranou proti duplicitám)

### Paměť
- **ShortTermMemory** – loguje každý vstup a odpověď (viz memory/short_term_memory.py)
- **LongTermMemory** – připravena pro vektorové uložení znalostí (viz memory/long_term_memory.py)

### Vývoj
- Pro přidání/změnu nástrojů editujte core/custom_tools.py a core/agents.py
- Pro rozšíření paměti viz memory/
- Pro testování použijte pytest

### Další
- Kód je PEP8, typované signatury, komentáře a docstringy
- Projekt je připraven pro týmové předání a další rozvoj