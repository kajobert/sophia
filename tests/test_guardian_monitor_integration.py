
from tests.conftest import robust_import, safe_remove
import tempfile
import os
import re
import pytest

sophia_monitor = robust_import('sophia_monitor')


def test_check_backend_crash_log_detects_error(request):
    # Vytvoříme dočasný log s chybou
    log_content = """
2025-09-16 12:00:00 - Něco proběhlo
2025-09-16 12:00:01 - Traceback (most recent call last):
2025-09-16 12:00:01 -   File \"main.py\", line 1, in <module>
2025-09-16 12:00:01 - ImportError: No module named 'foo'
2025-09-16 12:00:02 - Další zpráva
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write(log_content)
        fname = f.name
    try:
        result = sophia_monitor.check_backend_crash_log(log_path=fname, lines=10)
        # Musí vrátit poslední řádky a detekovat chybu
        assert "last_lines" in result
        assert "error_matches" in result
        # Musí najít ImportError a Traceback
        found_patterns = [pat for (_, _, pat) in result["error_matches"]]
        assert any(re.match(r"ImportError", pat) for pat in found_patterns)
        assert any(re.match(r"Traceback", pat) for pat in found_patterns)
        # Snapshot výstupu pro auditovatelnost
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot(str(result))
        else:
            # Ručně vytvořit auditní snapshot a označit test jako xfail
            import pathlib
            from conftest import ensure_snapshot_path
            base = pathlib.Path("tests/snapshots")
            base.mkdir(parents=True, exist_ok=True)
            snap_path = ensure_snapshot_path(base / "guardian_monitor_integration.approved.txt")
            snap_path.write_text(str(result), encoding="utf-8")
            pytest.xfail(f"Snapshot fixture nebyla dostupná, auditní snapshot byl vytvořen: {snap_path}. Zkontrolujte a potvrďte jeho obsah.")
    finally:
        safe_remove(fname)
