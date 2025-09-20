import pytest
import os

def test_env_file_write_blocked():
    # Pokus o zápis do produkčního .env musí být blokován a auditně zalogován
    env_path = os.path.abspath(".env")
    if not os.path.exists(env_path):
        pytest.skip(".env neexistuje v workspace")
    with pytest.raises(RuntimeError):
        with open(env_path, "w") as f:
            f.write("fail")

def test_watchdog_alive_write_blocked():
    # Pokus o zápis do watchdog.alive musí být blokován a auditně zalogován
    path = os.path.abspath("watchdog.alive")
    if not os.path.exists(path):
        pytest.skip("watchdog.alive neexistuje v workspace")
    with pytest.raises(RuntimeError):
        with open(path, "w") as f:
            f.write("fail")
