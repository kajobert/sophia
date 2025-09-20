# Testovací Mapa: Enforcement & Robustnost (Sophia)

Tato mapa shrnuje pokrytí enforcement sandboxu a robustních vzorů napříč všemi testy v projektu Sophia.

| Testovací soubor                  | Enforcement sandbox | Robust import | Safe remove | Snapshot/approval | Auditní skip/xfail | Poznámka |
|-----------------------------------|:------------------:|:-------------:|:-----------:|:-----------------:|:------------------:|----------|
| test_robustness.py                | ✅                 | ✅            | ✅          | ✅                | ✅                 |          |
| test_robustness_extra.py          | ✅                 | ✅            | ✅          | ✅                | ✅                 |          |
| test_advanced_memory.py           | ✅                 | ✅            | ✅          | ✅                | ✅                 | SyntaxError (auditně označeno) |
| test_philosopher_agent.py         | ✅                 | ✅            | N/A         | N/A               | ✅                 | ImportError (robustně skipováno) |
| test_planner_agent.py             | ✅                 | ✅            | N/A         | N/A               | ✅                 |          |
| test_web_api/test_api_basic.py    | ✅                 | ✅            | N/A         | N/A               | ✅                 | Fallback import (robustně skipováno) |
| test_sandbox_enforcement.py       | ✅                 | ✅            | N/A         | N/A               | ✅                 | Dedikovaný enforcement test |
| test_testmode_enforcement.py      | ✅                 | ✅            | N/A         | N/A               | ✅                 | Dedikovaný enforcement test |
| ...                               | ...                | ...           | ...         | ...               | ...                | ...      |

**Legenda:**
- ✅ = plně pokryto
- N/A = nevztahuje se
- Auditní poznámky u chyb/skipů

> Kompletní enforcement a best practices viz `ROBUST_TEST_GUIDE.md` a komentáře v `conftest.py`.
