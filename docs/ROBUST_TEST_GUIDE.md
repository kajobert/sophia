# Průvodce Robustními a Bezpečnými Testy (Sophia)

Tento dokument shrnuje best practices, vzory a konkrétní příklady pro psaní bezpečných, auditních a robustních testů v projektu Sophia.

## 1. Enforcement sandbox – základní pravidla
- Všechny testy jsou chráněny globální fixture (`enforce_test_mode_and_sandbox`) v `conftest.py`.
- Testy se spustí pouze s `SOPHIA_TEST_MODE=1`.
- Síť, zápis, procesy, DB, změny práv/času/env jsou blokovány a auditně logovány.
- Whitelistované proměnné a cesty jsou popsány v `conftest.py`.

## 2. Best practices
- Všechny externí importy přes `robust_import`.
- Mazání souborů pouze přes `safe_remove`.
- Snapshoty a approval soubory pouze v `tests/snapshots/`.
- Nikdy nemanipulovat s produkčními soubory ani `.env`.
- Každý skip/xfail musí být auditně zdokumentován.
- Síť/procesy/zápis pouze s auditním zdůvodněním a explicitním označením.

## 3. Příklady
```python
import pytest
from tests.conftest import robust_import, safe_remove

def test_example(request, snapshot):
    # ...testovací logika...
    pass

# Robustní import s fallbackem
try:
    import jwt
except ImportError:
    pytest.skip("jwt není dostupný", allow_module_level=True)
```

## 4. Auditní logika
- Každý pokus o zakázanou operaci je logován do výstupu testu.
- Všechny skipy/xfail jsou auditně dohledatelné.

## 5. Další zdroje
- Kompletní enforcement: komentáře v `tests/conftest.py`
- Auditní zápisy: `KNOWLEDGE_BASE.md`
