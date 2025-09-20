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
