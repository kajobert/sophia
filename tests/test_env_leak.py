import pytest
import os

def test_no_secret_env_in_snapshot(snapshot):
    # Ověř, že žádná citlivá proměnná prostředí se neobjeví ve snapshotu
    secret = os.environ.get("GEMINI_API_KEY")
    if not secret:
        pytest.skip("GEMINI_API_KEY není nastavena")
    snap = snapshot("env_check")
    assert secret not in snap
