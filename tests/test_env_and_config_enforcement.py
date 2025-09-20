import pytest
import os
import tempfile
import shutil

def test_readonly_env_blocked(tmp_path):
    # Simulace read-only .env
    env_path = tmp_path / ".env"
    env_path.write_text("SOME_KEY=1\n")
    os.chmod(env_path, 0o444)  # read-only
    try:
        with pytest.raises(PermissionError):
            with open(env_path, "w") as f:
                f.write("fail")
    finally:
        os.chmod(env_path, 0o666)


def test_corrupted_env_handling(tmp_path):
    # Poškozený .env
    env_path = tmp_path / ".env"
    env_path.write_text("\x00\x01\x02\n")
    # Očekáváme, že loader selže s ValueError nebo podobnou chybou
    from core import config
    with pytest.raises(Exception):
        config.load_env(str(env_path))


def test_invalid_yaml_config(tmp_path):
    # Nevalidní YAML
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(":- this is not valid yaml")
    from core import config
    with pytest.raises(Exception):
        config.load_yaml(str(yaml_path))


def test_missing_config_keys(tmp_path):
    # Chybějící klíče v configu
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text("key1: value1\n")
    from core import config
    with pytest.raises(KeyError):
        config.require_keys(str(yaml_path), ["key1", "key2"])  # key2 chybí


def test_timezone_change_blocked(monkeypatch):
    # Pokus o změnu časového pásma
    with pytest.raises(RuntimeError):
        os.environ["TZ"] = "Europe/Prague"
        if hasattr(time, "tzset"):
            import time
            time.tzset()


def test_env_var_change_blocked(monkeypatch):
    # Pokus o změnu proměnné mimo whitelist
    with pytest.raises(RuntimeError):
        os.putenv("DANGEROUS_VAR", "1")
    with pytest.raises(RuntimeError):
        os.environ["DANGEROUS_VAR"] = "1"
