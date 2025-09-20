import pytest
import os
import tempfile
from tests.conftest import robust_import

# --- Test: Test mode je povinný ---
import subprocess
def test_testmode_required():
    # Spustí pytest na tomto souboru bez SOPHIA_TEST_MODE a ověří, že enforcement selže
    env = os.environ.copy()
    env.pop("SOPHIA_TEST_MODE", None)
    result = subprocess.run([
        "pytest", "-v", __file__, "-k", "not test_testmode_required"
    ], env=env, capture_output=True, text=True)
    assert result.returncode == 2
    assert "SOPHIA_TEST_MODE není aktivní" in result.stdout or result.stderr

# --- Test: Není možné volat requests.get v test mode ---
def test_requests_blocked_in_testmode(monkeypatch):
    monkeypatch.setenv("SOPHIA_TEST_MODE", "1")
    import importlib
    importlib.reload(__import__("tests.conftest"))
    requests = robust_import("requests")
    with pytest.raises(RuntimeError):
        requests.get("https://example.com")

# --- Test: Není možné zapisovat mimo test adresář ---
def test_write_outside_testdir(monkeypatch):
    monkeypatch.setenv("SOPHIA_TEST_MODE", "1")
    import importlib
    importlib.reload(__import__("tests.conftest"))
    with pytest.raises(RuntimeError):
        with open("/etc/passwd", "w") as f:
            f.write("fail")

# --- Test: Zápis do /tmp je povolen ---
def test_write_tmp_allowed(monkeypatch):
    monkeypatch.setenv("SOPHIA_TEST_MODE", "1")
    import importlib
    importlib.reload(__import__("tests.conftest"))
    with tempfile.NamedTemporaryFile("w", dir="/tmp", delete=True) as f:
        f.write("ok")

# --- Test: Zápis do tests/ je povolen ---
def test_write_testsdir_allowed(monkeypatch):
    monkeypatch.setenv("SOPHIA_TEST_MODE", "1")
    import importlib
    importlib.reload(__import__("tests.conftest"))
    with open("tests/tmp_testfile.txt", "w") as f:
        f.write("ok")
    os.remove("tests/tmp_testfile.txt")
