import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import pytest
import os
import shutil
from guardian import (
    check_redis, check_celery, check_backend, check_audit_log, check_disk, check_llm_key,
    check_sandbox_integrity, check_config_files, rotate_audit_log, free_disk_space,
    reload_llm_key, restore_config_file, restore_env_file, restore_sandbox
)

def test_check_redis():
    assert isinstance(check_redis(), bool)

def test_check_celery():
    assert isinstance(check_celery(), bool)

def test_check_backend():
    assert isinstance(check_backend(), bool)

def test_check_audit_log():
    assert isinstance(check_audit_log(), bool)

def test_check_disk():
    assert isinstance(check_disk(), bool)

def test_check_llm_key():
    assert isinstance(check_llm_key(), bool)

def test_check_sandbox_integrity():
    assert isinstance(check_sandbox_integrity(), bool)

def test_check_config_files():
    assert isinstance(check_config_files(), bool)

def test_rotate_audit_log(tmp_path):
    log_path = tmp_path / "audit.log"
    with open(log_path, "w") as f:
        f.write("A" * 1024 * 1024 * 2)  # 2 MB
    assert rotate_audit_log(str(log_path), max_size_mb=1)
    assert os.path.exists(str(log_path) + ".bak")

def test_free_disk_space(tmp_path):
    log_dir = tmp_path / "logs"
    os.makedirs(log_dir)
    bak_file = log_dir / "test.log.bak"
    with open(bak_file, "w") as f:
        f.write("test")
    assert free_disk_space(str(tmp_path))
    assert not os.path.exists(bak_file)

def test_reload_llm_key():
    assert reload_llm_key()

def test_restore_config_file(tmp_path):
    backup = tmp_path / "config.yaml.bak"
    with open(backup, "w") as f:
        f.write("test")
    assert restore_config_file(str(tmp_path / "config.yaml"), str(backup))
    assert os.path.exists(tmp_path / "config.yaml")

def test_restore_env_file(tmp_path):
    backup = tmp_path / ".env.bak"
    with open(backup, "w") as f:
        f.write("test")
    assert restore_env_file(str(tmp_path / ".env"), str(backup))
    assert os.path.exists(tmp_path / ".env")

def test_restore_sandbox():
    assert restore_sandbox()
