import pytest



# Šablona pro parametrizované healthcheck testy
import pytest

# Seznam healthcheck funkcí a očekávaných výsledků
HEALTHCHECKS = [
    # (funkce, očekávaný výsledek, popis)
    # (sophia_monitor.check_redis, True, "Redis je dostupný"),
    # (sophia_monitor.check_celery, True, "Celery worker běží"),
    # (sophia_monitor.check_backend, True, "Backend API běží"),
    # (sophia_monitor.check_audit_log, True, "Audit log je dostupný"),
    # (sophia_monitor.check_disk, True, "Disk OK"),
    # (sophia_monitor.check_llm_key, True, "LLM klíč validní"),
]

@pytest.mark.parametrize("check_func,expected,desc", HEALTHCHECKS)
def test_healthchecks(check_func, expected, desc):
    """
    Parametrizovaný test pro všechny healthchecky.
    check_func: funkce, která provádí healthcheck
    expected: očekávaný výsledek (True/False nebo Exception)
    desc: popis testovaného scénáře
    """
    # Výsledek healthchecku
    result = check_func()
    assert result == expected, f"{desc}: očekáváno {expected}, dostal {result}"


@pytest.mark.skip(
    reason="Kontrola check_sandbox_integrity není implementována v sophia_monitor.py"
)
def test_check_sandbox_integrity():
    pass


@pytest.mark.skip(
    reason="Kontrola check_config_files není implementována v sophia_monitor.py"
)
def test_check_config_files():
    pass


@pytest.mark.skip(reason="rotate_audit_log není implementována v sophia_monitor.py")
def test_rotate_audit_log(tmp_path):
    pass


@pytest.mark.skip(reason="free_disk_space není implementována v sophia_monitor.py")
def test_free_disk_space(tmp_path):
    pass


@pytest.mark.skip(reason="reload_llm_key není implementována v sophia_monitor.py")
def test_reload_llm_key():
    pass


@pytest.mark.skip(reason="restore_config_file není implementována v sophia_monitor.py")
def test_restore_config_file(tmp_path):
    pass


@pytest.mark.skip(reason="restore_env_file není implementována v sophia_monitor.py")
def test_restore_env_file(tmp_path):
    pass


@pytest.mark.skip(reason="restore_sandbox není implementována v sophia_monitor.py")
def test_restore_sandbox():
    pass
