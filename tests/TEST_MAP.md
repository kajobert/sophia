# Mapa a katalog testů projektu Sophia

Tento dokument slouží jako centrální přehled všech testů v adresáři `tests/`.
Obsahuje:
- Seznam všech testovacích souborů
- Stručný popis účelu každého testu
- Poznámky k robustním vzorům a šablonám
- Odkazy na inline šablony v komentářích testů

---

## Seznam testovacích souborů a jejich účel

### test_advanced_memory.py
Testuje pokročilé funkce paměťového subsystému (např. advanced_memory, inmemory_redis). Ověřuje robustnost ukládání, načítání a mazání dat v paměti.

### test_agents_integration.py
Ověřuje integraci a spolupráci jednotlivých agentů v systému Sophia. Zaměřuje se na komunikační toky a správné předávání úloh.

### test_aider_agent.py
Testuje chování AiderAgenta, včetně robustního návrhu změn a auditování. Používá approval snapshoty pro ověření výstupu.

### test_architect_agent.py
Testuje inicializaci a základní funkce ArchitectAgenta.

### test_autogen_team.py
Ověřuje týmovou spolupráci agentů v režimu autogen.

### test_code_executor.py, test_code_executor_tool.py
Testují robustní spouštění a auditování kódu v sandboxu.

### test_consciousness_loop.py
Základní šablona pro testování hlavní smyčky vědomí Sophia. (viz komentář v souboru)

### test_engineer_agent.py
Šablona pro testování EngineerAgenta. (viz komentář v souboru)

### test_ethos_module.py
Šablona pro testování EthosModule a plánovacího cyklu. (viz komentář v souboru)

### test_file_system.py, test_file_system_tool.py
Testují bezpečnost a robustnost souborových operací.

### test_gemini_llm_adapter.py
Testuje integraci s LLM Gemini.

### test_guardian_basic.py, test_guardian_healthchecks.py, test_guardian_monitor_integration.py
Testují základní, healthcheck a integrační funkce Guardian agenta.

### test_inmemory_redis.py
Testuje robustní práci s in-memory Redis vrstvou.

### test_integration_security.py
Šablona pro integrační a bezpečnostní testy (viz komentář v souboru).

### test_llm_cache.py, test_llm_imports.py
Testují správné cachování a importy LLM.

### test_memory_tools.py
Testuje pomocné nástroje pro práci s pamětí.

### test_orchestrator_cycle.py
Testuje orchestraci cyklu agentů.

### test_philosopher_agent.py
Testuje základní funkce PhilosopherAgenta.

### test_planner_agent.py
Testuje základní funkce PlannerAgenta.

### test_robustness.py, test_robustness_app.py
Testy chybových stavů a robustnosti systému.

### test_sophia_monitor.py
Testuje monitorovací funkce Sophia.

### test_system_awareness.py
Testuje systémové povědomí a self-checky.

### test_utils.py
Testuje pomocné utility.

---

## Robustní šablony a vzory

### Inline šablony v testech
- `test_ethos_module.py` – šablona pro robustní testování EthosModule a plánovacího cyklu
- `test_engineer_agent.py` – šablona pro robustní testování EngineerAgenta
- `test_consciousness_loop.py` – šablona pro robustní testování hlavní smyčky

Každá šablona obsahuje vzor použití `robust_import`, `snapshot`, `request` a další robustní vzory.

### Doporučení
- Pro nové testy vždy vycházejte z těchto inline šablon.
- Pravidla a doporučené signatury najdete v `ROBUST_TEST_GUIDE.md`.

---

Tento katalog udržujte aktuální a rozšiřujte při přidání nových testů nebo šablon.
