import os
import tempfile
import os
import tempfile
import sys
import pytest
from tests.conftest import safe_remove, robust_import
 
sophia_monitor = robust_import('sophia_monitor')

def test_scan_logs_for_errors_detects_pattern(request):
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
        safe_remove(fname)
        # Snapshot výstupu hashů
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot(str(hashes))
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("ERROR\nERROR\nERROR\n")
        fname = f.name
    try:
        result = sophia_monitor.scan_logs_for_errors(
            [fname], patterns=[r"ERROR"], min_count=3
        )
        assert any(fname in k[0] for k in result.keys())
    finally:
        safe_remove(fname)
        # Snapshot výstupu logu
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot(str(result))


def test_check_internet_connectivity():
    # Očekáváme True nebo False, podle připojení
    assert isinstance(sophia_monitor.check_internet_connectivity(), bool)


def test_check_dns_resolution():
    assert isinstance(sophia_monitor.check_dns_resolution(), bool)
