import pytest

# --- Šablona pro testy chybových stavů a robustnosti Sophia ---


import subprocess
import os
import shutil
import tempfile
import time

def test_db_unavailable():
    """Simuluje výpadek DB: backend by měl selhat a zalogovat chybu."""
    # Předpoklad: backend lze spustit přes příkaz a loguje do souboru
    # Zde pouze ukázka, nutno upravit podle konkrétního startu backendu
    # 1. Zastavit DB (nebo nastavit špatné DB parametry)
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql://wrong:wrong@localhost:5432/wrong"
    log_path = "test_db_unavailable.log"
    try:
        with open(log_path, "w") as logf:
            proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
            time.sleep(3)
            proc.terminate()
        with open(log_path) as f:
            log = f.read()
        assert "error" in log.lower() or "fail" in log.lower()
    finally:
        if os.path.exists(log_path):
            os.remove(log_path)

# 2. Chybějící nebo nevalidní .env

def test_missing_env_file():
    """Spuštění aplikace bez .env by mělo failnout a zalogovat chybu."""
    import sys
    import copy
    import tempfile
    # Uložíme snapshot prostředí
    env_snapshot = copy.deepcopy(os.environ)
    try:
        # Vytvoříme dočasnou neexistující cestu pro .env
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_env_path = os.path.join(tmpdir, "nonexistent.env")
            os.environ["SOPHIA_ENV_PATH"] = missing_env_path
            result = subprocess.run([
                sys.executable, "tests/test_robustness_app.py"
            ], capture_output=True, text=True, env=os.environ)
            assert ".env soubor nebyl nalezen" in result.stdout or ".env soubor nebyl nalezen" in result.stderr
    finally:
        # Obnovíme snapshot prostředí
        os.environ.clear()
        os.environ.update(env_snapshot)
    # Test main.py byl odstraněn – robustnost .env testujeme pouze přes oddělený entrypoint.


def test_invalid_env_values():
    """Spuštění s nevalidními hodnotami v .env by mělo failnout nebo zalogovat chybu."""
    import tempfile
    import sys
    # Vytvoříme dočasný .env s nevalidními hodnotami
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env_path = os.path.join(tmpdir, "test.env")
        with open(fake_env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=\nSECRET_KEY=\n")
        env = os.environ.copy()
        env["SOPHIA_ENV_PATH"] = fake_env_path
        log_path = "test_invalid_env_values.log"
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
                time.sleep(3)
                proc.terminate()
            with open(log_path) as f:
                log = f.read()
            assert "invalid" in log.lower() or "fail" in log.lower() or "error" in log.lower()
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

# 3. Špatné proměnné prostředí

def test_invalid_env_vars():
    """Špatné proměnné prostředí by měly způsobit fail nebo zalogovat chybu."""
    env = os.environ.copy()
    env["GOOGLE_CLIENT_ID"] = ""
    env["SECRET_KEY"] = ""
    log_path = "test_invalid_env_vars.log"
    try:
        with open(log_path, "w") as logf:
            proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
            time.sleep(3)
            proc.terminate()
        with open(log_path) as f:
            log = f.read()
        assert "invalid" in log.lower() or "fail" in log.lower() or "error" in log.lower()
    finally:
        if os.path.exists(log_path):
            os.remove(log_path)

# 4. Selhání služeb (orchestrátor, agenti)

def test_service_failure():
    """Simulace selhání služby (např. orchestrátor, agent) – ověřit logování chyby."""
    # Zde pouze ukázka, nutno upravit podle konkrétního startu služby
    # Například spustit orchestrátor s nevalidní konfigurací
    env = os.environ.copy()
    env["ORCHESTRATOR_CONFIG"] = "invalid"
    log_path = "test_service_failure.log"
    try:
        with open(log_path, "w") as logf:
            proc = subprocess.Popen(["python3", "core/orchestrator.py"], env=env, stdout=logf, stderr=logf)
            time.sleep(3)
            proc.terminate()
        with open(log_path) as f:
            log = f.read()
        assert "error" in log.lower() or "fail" in log.lower()
    finally:
        if os.path.exists(log_path):
            os.remove(log_path)

# 5. Logování chyb

def test_error_logging():
    """Ověř, že všechny chyby jsou zalogovány s detailem a časem (kontrola log souboru)."""
    # Předpoklad: logy jsou v logs/guardian.log nebo sophia_main.log
    log_paths = ["logs/guardian.log", "logs/sophia_main.log"]
    found = False
    for log_path in log_paths:
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = f.read().lower()
                if "error" in log or "fail" in log or "traceback" in log:
                    found = True
    assert found, "V logu nebyla nalezena žádná chyba."

# 6. Watchdog .env

def test_env_watchdog_backup():
    """Ověř, že při změně .env vznikne záloha v .env_backups/ a je zalogována."""
    """
    Tento test je závislý na heartbeat souboru watchdogu (watchdog.alive).
    Všechny dočasné soubory ukládá do tests/tmp/.
    Test nikdy nesmaže watchdog.alive.
    """
    import sys
    import datetime
    import json
    TMPDIR = os.path.join("tests", "tmp")
    os.makedirs(TMPDIR, exist_ok=True)
    heartbeat_path = os.path.join(os.getcwd(), "watchdog.alive")
    # Ověř existenci a validitu heartbeat souboru
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
    # Pracujeme pouze s dočasnou kopií .env v tests/tmp
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
    env = os.environ.copy()
    env["SOPHIA_ENV_PATH"] = fake_env_path
    env["SOPHIA_ENV_BACKUP_DIR"] = backup_dir
    proc = subprocess.Popen([sys.executable, "main.py"], env=env)
    time.sleep(5)
    proc.terminate()
    try:
        after = set(os.listdir(backup_dir))
    except Exception as e:
        pytest.skip(f"Nelze číst backup dir po testu: {e}")
    # Logujeme snapshoty
    log_path = os.path.join(TMPDIR, "watchdog_test.log")
    with open(log_path, "a") as logf:
        logf.write(f"[{datetime.datetime.now()}] before: {before}\n")
        logf.write(f"[{datetime.datetime.now()}] after: {after}\n")
    assert len(after) > len(before), "Záloha .env nebyla vytvořena."

# 7. Integrita konfigurace

def test_config_integrity():
    """Ověř, že změna .env/config.yaml je detekována a správně zalogována (např. v guardian.log)."""
    # Změnit .env nebo config.yaml a ověřit log
    import tempfile
    import sys
    log_path = "logs/guardian.log"
    if not os.path.exists(log_path):
        pytest.skip("Log guardian.log neexistuje")
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env_path = os.path.join(tmpdir, "test.env")
        with open(fake_env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=abc\nSECRET_KEY=def\n# test_config_integrity\n")
        env = os.environ.copy()
        env["SOPHIA_ENV_PATH"] = fake_env_path
        proc = subprocess.Popen([sys.executable, "main.py"], env=env)
        time.sleep(3)
        proc.terminate()
    with open(log_path) as f:
        log = f.read().lower()
    assert "config" in log or "env" in log or "integrity" in log, "Změna nebyla zalogována."
