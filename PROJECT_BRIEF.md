# PROJECT_BRIEF.md

## Projekt Sophia – Stav, architektura a doporučení (září 2025)

### Přehled
Sophia je autonomní agent postavený na CrewAI, zaměřený na bezpečné, auditovatelné a rozšiřitelné zpracování úloh s podporou webového vyhledávání, práce se soubory a duální paměti (krátkodobá i dlouhodobá). Projekt je připraven pro týmový vývoj a další rozšiřování.

---

### Aktuální stav
- **Kód je vyčištěn od testovacích a dočasných souborů.**
- **main.py**: Interaktivní smyčka, loguje každý vstup a odpověď do krátkodobé paměti.
- **Paměť**: Krátkodobá (episodická) paměť je aktivní, dlouhodobá (vektorová, ChromaDB) připravena k integraci.
- **Nástroje**: WebSearchTool (Serper), FileWriteTool, FileReadTool, FileEditTool – všechny robustní, testované, bez duplikací a chyb.
- **Agent**: developer_agent má registrovány všechny nástroje, je připraven na další rozšiřování.
- **Dokumentace**: README.md, AGENTS.md a requirements.txt jsou aktuální a reflektují skutečný stav projektu.

---

### Vyřešené problémy
- **Duplikace a nepořádek v nástrojích**: Všechny file tools byly sjednoceny a zjednodušeny, FileEditTool nyní chrání proti duplicitnímu zápisu.
- **Chyby v předávání dat mezi úkoly**: Architektura byla převedena na čistý interaktivní režim, kde je každý úkol jasně oddělen.
- **Legacy a duplicity v kódu**: main.py, agents.py i custom_tools.py byly vyčištěny od starých a duplicitních částí.
- **Testovací a dočasné soubory**: Všechny byly odstraněny, workspace je čistý.
- **WebSearchTool**: Opraveno předávání argumentů, nyní funguje spolehlivě.

---

### Doporučení pro další vývoj
- **Integrace long-term memory**: Doplnit využití vektorové paměti v hlavní smyčce (např. ukládání odpovědí, vyhledávání relevantních vzpomínek).
- **Pokrytí testy**: Doplnit/rozšířit unit a integrační testy, případně CI pipeline.
- **Role a více agentů**: Připravit scénáře pro více agentů a specializované role.
- **Bezpečnost a audit**: Zvážit auditní logování a bezpečnostní review před nasazením do produkce.
- **Dokumentace**: Pravidelně aktualizovat README, AGENTS a další dokumenty při každé větší změně.

---

### Struktura projektu (září 2025)

- main.py
- core/
  - agents.py
  - custom_tools.py
  - tasks.py
- memory/
  - short_term_memory.py
  - long_term_memory.py
  - memory_manager.py
- tools/
- logs/
- requirements.txt
- README.md
- AGENTS.md
- config.yaml
- tool_config.json
- tool_input.json

---

### Kontakty a předání
Projekt je připraven pro týmové předání. Všechny klíčové části jsou zdokumentovány a připraveny k dalšímu rozvoji. V případě dotazů kontaktujte původního maintenera nebo použijte komentáře v kódu.

---

*Vygenerováno GitHub Copilotem na základě aktuálního stavu workspace a požadavků zadavatele.*
