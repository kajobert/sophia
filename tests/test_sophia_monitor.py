import os
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))
import sophia_monitor


def test_check_integrity_creates_hashes():
    # Vytvoříme dočasný soubor v rootu workspace, aby byl zachycen globem
    fname = "test_temp_sophiamonitor.py"
    with open(fname, "w") as f:
        f.write('print("test")')
    try:
        hashes = sophia_monitor.check_integrity()
        assert isinstance(hashes, dict)
        assert fname in hashes
        assert hashes[fname] is not None
    finally:
        os.remove(fname)


def test_scan_logs_for_errors_detects_pattern():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("ERROR\nERROR\nERROR\n")
        fname = f.name
    try:
        result = sophia_monitor.scan_logs_for_errors(
            [fname], patterns=[r"ERROR"], min_count=3
        )
        assert any(fname in k[0] for k in result.keys())
    finally:
        os.remove(fname)


def test_check_internet_connectivity():
    # Očekáváme True nebo False, podle připojení
    assert isinstance(sophia_monitor.check_internet_connectivity(), bool)


def test_check_dns_resolution():
    assert isinstance(sophia_monitor.check_dns_resolution(), bool)
