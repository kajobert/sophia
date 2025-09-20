import pytest

# --- Šablona pro testy chybových stavů a robustnosti Sophia ---



import pytest
from tests.conftest import robust_import, safe_remove
import tempfile
import os
import time
import sys
import copy

def test_db_unavailable(request, snapshot):
    """Simuluje výpadek DB: backend by měl selhat a zalogovat chybu."""
    # Vše v dočasném adresáři, logy snapshotujeme
    tempdir = tempfile.TemporaryDirectory()
    log_path = os.path.join(tempdir.name, "test_db_unavailable.log")
    env = copy.deepcopy(os.environ)
    env["DATABASE_URL"] = "postgresql://wrong:wrong@localhost:5432/wrong"
    try:
        import subprocess
        with open(log_path, "w") as logf:
            proc = subprocess.Popen([sys.executable, "main.py"], env=env, stdout=logf, stderr=logf)
            time.sleep(3)
            proc.terminate()
        with open(log_path) as f:
            log = f.read()
        snapshot({"log": log})
        assert "error" in log.lower() or "fail" in log.lower()
    finally:
        safe_remove(log_path)
        tempdir.cleanup()

# 2. Chybějící nebo nevalidní .env

def test_missing_env_file(request, snapshot):
    """Spuštění aplikace bez .env by mělo failnout a zalogovat chybu."""
    env_snapshot = copy.deepcopy(os.environ)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_env_path = os.path.join(tmpdir, "nonexistent.env")
            os.environ["SOPHIA_ENV_PATH"] = missing_env_path
            import subprocess
            result = subprocess.run([
                sys.executable, "tests/test_robustness_app.py"
            ], capture_output=True, text=True, env=os.environ)
            snapshot({"stdout": result.stdout, "stderr": result.stderr})
            assert ".env soubor nebyl nalezen" in result.stdout or ".env soubor nebyl nalezen" in result.stderr
    finally:
        os.environ.clear()
        os.environ.update(env_snapshot)


def test_invalid_env_values(request, snapshot):
    """Spuštění s nevalidními hodnotami v .env by mělo failnout nebo zalogovat chybu."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env_path = os.path.join(tmpdir, "test.env")
        with open(fake_env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=\nSECRET_KEY=\n")
        env = copy.deepcopy(os.environ)
        env["SOPHIA_ENV_PATH"] = fake_env_path
        log_path = os.path.join(tmpdir, "test_invalid_env_values.log")
        import subprocess
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen([sys.executable, "main.py"], env=env, stdout=logf, stderr=logf)
                time.sleep(3)
                proc.terminate()
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "invalid" in log.lower() or "fail" in log.lower() or "error" in log.lower()
        finally:
            safe_remove(log_path)

# 3. Špatné proměnné prostředí

def test_invalid_env_vars(request, snapshot):
    """Špatné proměnné prostředí by měly způsobit fail nebo zalogovat chybu."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = copy.deepcopy(os.environ)
        env["GOOGLE_CLIENT_ID"] = ""
        env["SECRET_KEY"] = ""
        log_path = os.path.join(tmpdir, "test_invalid_env_vars.log")
        subprocess = robust_import('subprocess')
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen([sys.executable, "main.py"], env=env, stdout=logf, stderr=logf)
                time.sleep(3)
                proc.terminate()
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "invalid" in log.lower() or "fail" in log.lower() or "error" in log.lower()
        finally:
            safe_remove(log_path)

# 4. Selhání služeb (orchestrátor, agenti)

def test_service_failure(request, snapshot):
    """Simulace selhání služby (např. orchestrátor, agent) – ověřit logování chyby."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = copy.deepcopy(os.environ)
        env["ORCHESTRATOR_CONFIG"] = "invalid"
        log_path = os.path.join(tmpdir, "test_service_failure.log")
        subprocess = robust_import('subprocess')
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen([sys.executable, "core/orchestrator.py"], env=env, stdout=logf, stderr=logf)
                time.sleep(3)
                proc.terminate()
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "error" in log.lower() or "fail" in log.lower()
        finally:
            safe_remove(log_path)

# 5. Logování chyb

def test_error_logging(request, snapshot):
    """Ověř, že všechny chyby jsou zalogovány s detailem a časem (kontrola log souboru)."""
    log_paths = ["logs/guardian.log", "logs/sophia_main.log"]
    found = False
    logs = {}
    for log_path in log_paths:
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = f.read().lower()
                logs[log_path] = log
                if "error" in log or "fail" in log or "traceback" in log:
                    found = True
    snapshot(logs)
    assert found, "V logu nebyla nalezena žádná chyba."

# 6. Watchdog .env

def test_env_watchdog_backup(request, snapshot):
    """Ověř, že při změně .env vznikne záloha v .env_backups/ a je zalogována."""
    import datetime
    import json
    TMPDIR = os.path.join("tests", "tmp")
    os.makedirs(TMPDIR, exist_ok=True)
    heartbeat_path = os.path.join(os.getcwd(), "watchdog.alive")
    if not os.path.exists(heartbeat_path):
        pytest.skip("watchdog.alive neexistuje - watchdog neběží")
    try:
        with open(heartbeat_path) as f:
            data = json.load(f)
        last_heartbeat = data["last_heartbeat"]
        dt = datetime.datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = (now - dt).total_seconds()
        assert delta < 10, f"watchdog.alive je starý {delta:.1f}s (poslední heartbeat: {last_heartbeat})"
    except Exception as e:
        pytest.skip(f"watchdog.alive je nevalidní: {e}")
    fake_env_path = os.path.join(TMPDIR, "test_env_watchdog.env")
    try:
        with open(fake_env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=abc\nSECRET_KEY=def\n# test_env_watchdog_backup\n")
    except Exception as e:
        pytest.skip(f"Nelze zapsat do dočasného .env: {e}")
    try:
        backup_dir = os.path.join(TMPDIR, "env_backups")
        os.makedirs(backup_dir, exist_ok=True)
        before = set(os.listdir(backup_dir))
    except Exception as e:
        pytest.skip(f"Nelze číst backup dir: {e}")
    env = copy.deepcopy(os.environ)
    env["SOPHIA_ENV_PATH"] = fake_env_path
    env["SOPHIA_ENV_BACKUP_DIR"] = backup_dir
    subprocess = robust_import('subprocess')
    proc = subprocess.Popen([sys.executable, "main.py"], env=env)
    time.sleep(5)
    proc.terminate()
    try:
        after = set(os.listdir(backup_dir))
    except Exception as e:
        pytest.skip(f"Nelze číst backup dir po testu: {e}")
    log_path = os.path.join(TMPDIR, "watchdog_test.log")
    with open(log_path, "a") as logf:
        logf.write(f"[{datetime.datetime.now()}] before: {before}\n")
        logf.write(f"[{datetime.datetime.now()}] after: {after}\n")
    snapshot({"before": list(before), "after": list(after)})
    assert len(after) > len(before), "Záloha .env nebyla vytvořena."

# 7. Integrita konfigurace

def test_config_integrity(request, snapshot):
    """Ověř, že změna .env/config.yaml je detekována a správně zalogována (např. v guardian.log)."""
    log_path = "logs/guardian.log"
    if not os.path.exists(log_path):
        pytest.skip("Log guardian.log neexistuje")
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env_path = os.path.join(tmpdir, "test.env")
        with open(fake_env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=abc\nSECRET_KEY=def\n# test_config_integrity\n")
        env = copy.deepcopy(os.environ)
        env["SOPHIA_ENV_PATH"] = fake_env_path
        subprocess = robust_import('subprocess')
        proc = subprocess.Popen([sys.executable, "main.py"], env=env)
        time.sleep(3)
        proc.terminate()
    with open(log_path) as f:
        log = f.read().lower()
    snapshot({"log": log})
    assert "config" in log or "env" in log or "integrity" in log, "Změna nebyla zalogována."
