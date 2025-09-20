import pytest
import logging

def test_skip_audit_log(caplog):
    with caplog.at_level(logging.WARNING):
        pytest.skip("Auditní skip testu")
    assert any("audit" in r.lower() or "skip" in r.lower() for r in caplog.text.splitlines())

def test_xfail_audit_log(caplog):
    with caplog.at_level(logging.WARNING):
        pytest.xfail("Auditní xfail testu")
    assert any("audit" in r.lower() or "xfail" in r.lower() for r in caplog.text.splitlines())
