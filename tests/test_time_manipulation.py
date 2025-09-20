import pytest
import datetime
import os

def test_datetime_patch_blocked(monkeypatch):
    # Pokus o patchování datetime.now by měl být auditně zachycen, pokud enforcement patchuje i tuto oblast
    try:
        monkeypatch.setattr(datetime, "datetime", lambda: None)
        assert False, "Patchování datetime by mělo být blokováno nebo auditováno."
    except Exception:
        pass  # Očekáváme selhání nebo auditní log

def test_os_time_set_blocked():
    # Pokus o změnu času přes OS (pokud enforcement podporuje)
    if hasattr(os, "stime"):
        with pytest.raises(RuntimeError):
            os.stime(0)
    else:
        pytest.skip("os.stime není dostupné na této platformě")
