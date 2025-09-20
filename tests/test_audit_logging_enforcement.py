import pytest
import os
import io
import logging

def test_audit_log_on_blocked_write(tmp_path, caplog):
    # Pokus o zápis mimo povolenou cestu musí být auditně zalogován
    blocked_path = "/root/forbidden.txt"
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError):
            with open(blocked_path, "w") as f:
                f.write("fail")
    assert any("audit" in r.lower() or "blokováno" in r.lower() for r in caplog.text.splitlines())


def test_audit_log_on_blocked_network(caplog):
    import socket
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError):
            socket.socket()
    assert any("audit" in r.lower() or "blokováno" in r.lower() for r in caplog.text.splitlines())


def test_audit_log_on_blocked_env(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING):
        with pytest.raises(RuntimeError):
            os.putenv("DANGEROUS_VAR", "1")
    assert any("audit" in r.lower() or "blokováno" in r.lower() for r in caplog.text.splitlines())
