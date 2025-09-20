import pytest
import tempfile
import os
import copy
from tests.conftest import robust_import, safe_remove

# --- 1. Test: Změna práv souboru .env (read-only) ---
def test_env_file_readonly(request, snapshot):
    """Ověř, že aplikace správně zaloguje chybu při read-only .env souboru."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, "test.env")
        with open(env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=abc\nSECRET_KEY=def\n")
        os.chmod(env_path, 0o444)  # read-only
        env = copy.deepcopy(os.environ)
        env["SOPHIA_ENV_PATH"] = env_path
        subprocess = robust_import('subprocess')
        log_path = os.path.join(tmpdir, "readonly_env.log")
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
                proc.wait(timeout=5)
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "permission" in log.lower() or "read-only" in log.lower() or "error" in log.lower()
        finally:
            safe_remove(log_path)
            os.chmod(env_path, 0o666)

# --- 2. Test: Poškozený .env (binární obsah) ---
def test_env_file_corrupted(request, snapshot):
    """Ověř, že aplikace zaloguje chybu při poškozeném .env souboru (binární data)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, "test.env")
        with open(env_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        env = copy.deepcopy(os.environ)
        env["SOPHIA_ENV_PATH"] = env_path
        subprocess = robust_import('subprocess')
        log_path = os.path.join(tmpdir, "corrupted_env.log")
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
                proc.wait(timeout=5)
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "error" in log.lower() or "decode" in log.lower() or "invalid" in log.lower()
        finally:
            safe_remove(log_path)

# --- 3. Test: Změna config.yaml na nevalidní YAML ---
def test_invalid_config_yaml(request, snapshot):
    """Ověř, že aplikace zaloguje chybu při nevalidním YAML v config.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")
        with open(config_path, "w") as f:
            f.write(":- this is not valid yaml\nfoo: [bar\n")
        env = copy.deepcopy(os.environ)
        env["SOPHIA_CONFIG_PATH"] = config_path
        subprocess = robust_import('subprocess')
        log_path = os.path.join(tmpdir, "invalid_yaml.log")
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
                proc.wait(timeout=5)
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "yaml" in log.lower() or "parse" in log.lower() or "error" in log.lower()
        finally:
            safe_remove(log_path)

# --- 4. Test: Chybějící klíč v .env (např. chybí SECRET_KEY) ---
def test_env_missing_key(request, snapshot):
    """Ověř, že aplikace zaloguje chybu při chybějícím klíči v .env."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = os.path.join(tmpdir, "test.env")
        with open(env_path, "w") as f:
            f.write("GOOGLE_CLIENT_ID=abc\n")  # SECRET_KEY chybí
        env = copy.deepcopy(os.environ)
        env["SOPHIA_ENV_PATH"] = env_path
        subprocess = robust_import('subprocess')
        log_path = os.path.join(tmpdir, "missing_key.log")
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
                proc.wait(timeout=5)
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "secret_key" in log.lower() or "missing" in log.lower() or "error" in log.lower()
        finally:
            safe_remove(log_path)

# --- 5. Test: Změna časové zóny v prostředí ---
def test_timezone_change(request, snapshot):
    """Ověř, že aplikace správně loguje a funguje při změně časové zóny."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = copy.deepcopy(os.environ)
        env["TZ"] = "Pacific/Honolulu"
        subprocess = robust_import('subprocess')
        log_path = os.path.join(tmpdir, "timezone.log")
        try:
            with open(log_path, "w") as logf:
                proc = subprocess.Popen(["python3", "main.py"], env=env, stdout=logf, stderr=logf)
                proc.wait(timeout=5)
            with open(log_path) as f:
                log = f.read()
            snapshot({"log": log})
            assert "honolulu" in log.lower() or "timezone" in log.lower() or "error" not in log.lower()
        finally:
            safe_remove(log_path)

# --- 6. Test: Pokus o zápis do chráněného souboru (.env v rootu projektu) ---
def test_write_protected_env_root(snapshot):
    """Ověř, že zápis do produkčního .env v rootu je blokován a zalogován."""
    import os
    protected_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    try:
        with open(protected_env, "a") as f:
            f.write("SHOULD_NOT_WRITE=1\n")
        result = "Zápis povolen (CHYBA)"
    except Exception as e:
        result = f"Blokováno: {e}"
    snapshot(result)
    # Ověř auditní log
    audit_log = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp', 'sandbox_audit.log'))
    if os.path.exists(audit_log):
        with open(audit_log) as f:
            log = f.read()
        snapshot({"audit_log": log})

# --- 7. Test: Pokus o síťovou komunikaci ---
def test_network_access_blocked(snapshot):
    import socket
    try:
        s = socket.socket()
        s.connect(("example.com", 80))
        result = "Síťové spojení povoleno (CHYBA)"
    except Exception as e:
        result = f"Blokováno: {e}"
    snapshot(result)

# --- 8. Test: Pokus o spawn procesu ---
def test_spawn_process_blocked(snapshot):
    import subprocess
    try:
        subprocess.Popen(["echo", "test"])
        result = "Spawn procesu povolen (CHYBA)"
    except Exception as e:
        result = f"Blokováno: {e}"
    snapshot(result)

# --- 9. Test: Pokus o změnu práv souboru mimo sandbox ---
def test_chmod_outside_sandbox_blocked(snapshot):
    import os
    protected = "/etc/passwd"
    try:
        os.chmod(protected, 0o777)
        result = "Změna práv povolena (CHYBA)"
    except Exception as e:
        result = f"Blokováno: {e}"
    snapshot(result)

# --- 10. Test: Pokus o změnu env proměnné mimo whitelist ---
def test_env_var_change_blocked(snapshot):
    import os
    try:
        os.environ["LD_LIBRARY_PATH"] = "/tmp"
        result = "Změna env proměnné povolena (CHYBA)"
    except Exception as e:
        result = f"Blokováno: {e}"
    snapshot(result)

# --- 11. Test: Pokus o zápis mimo povolené složky ---
def test_write_outside_allowed_dirs_blocked(snapshot):
    try:
        with open("/etc/sophia_test", "w") as f:
            f.write("fail")
        result = "Zápis povolen (CHYBA)"
    except Exception as e:
        result = f"Blokováno: {e}"
    snapshot(result)

# --- 12. Test: Integrity auditního logu ---
def test_audit_log_integrity(snapshot):
    import os
    audit_log = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp', 'sandbox_audit.log'))
    if os.path.exists(audit_log):
        with open(audit_log) as f:
            log = f.read()
        snapshot({"audit_log": log})
    else:
        snapshot("Audit log neexistuje")

# --- 13. Test: Pokus o import nebezpečných modulů ---
def test_import_dangerous_modules_blocked(snapshot):
    dangerous = ["ctypes", "resource", "fcntl", "signal"]
    results = {}
    for mod in dangerous:
        try:
            __import__(mod)
            results[mod] = "Import povolen (CHYBA)"
        except Exception as e:
            results[mod] = f"Blokováno: {e}"
    snapshot(results)

# --- 14. Test: Simulace selhání enforcementu sandboxu ---
def test_sandbox_enforcement_failure(snapshot):
    # Simulace: enforcement fixture je vypnuta (tento test pouze loguje varování)
    # V reálném běhu by testy bez enforcementu měly selhat, zde pouze ověříme, že je to detekovatelné
    import os
    enforcement_active = os.environ.get("SOPHIA_TEST_MODE") == "1"
    if not enforcement_active:
        result = "ENFORCEMENT SELHAL: Testy běží bez sandboxu! (CHYBA)"
    else:
        result = "Enforcement aktivní, sandbox chrání."
    snapshot(result)

# --- 15. Test: Race condition při paralelním zápisu do snapshotů ---
def test_snapshot_race_condition(snapshot, tmp_path):
    import threading
    import pathlib
    import time
    base = pathlib.Path("tests/snapshots")
    approved = base / "race_condition.approved.txt"
    received = base / "race_condition.received.txt"
    def write_snapshot(content):
        for _ in range(5):
            received.write_text(content)
            time.sleep(0.01)
    t1 = threading.Thread(target=write_snapshot, args=("A",))
    t2 = threading.Thread(target=write_snapshot, args=("B",))
    t1.start(); t2.start(); t1.join(); t2.join()
    # Ověř, že snapshot není poškozen (obsah je buď A nebo B, ne mix)
    val = received.read_text()
    if val.strip() not in ("A", "B"):
        result = f"Race condition: obsah snapshotu poškozen: {val}"
    else:
        result = f"OK: {val}"
    snapshot(result)
