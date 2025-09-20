import pytest
import os

def test_whitelisted_env_var(monkeypatch):
    # Ověř, že whitelisted proměnná prostředí lze změnit
    whitelisted = "PYTHONPATH"
    try:
        os.putenv(whitelisted, "test")
        os.environ[whitelisted] = "test"
    except RuntimeError:
        pytest.fail(f"Whitelisted proměnná {whitelisted} byla blokována enforcementem!")
