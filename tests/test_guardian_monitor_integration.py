import sophia_monitor
import tempfile
import os
import re

def test_check_backend_crash_log_detects_error():
    # Vytvoříme dočasný log s chybou
    log_content = """
2025-09-16 12:00:00 - Něco proběhlo
2025-09-16 12:00:01 - Traceback (most recent call last):
2025-09-16 12:00:01 -   File \"main.py\", line 1, in <module>
2025-09-16 12:00:01 - ImportError: No module named 'foo'
2025-09-16 12:00:02 - Další zpráva
"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write(log_content)
        fname = f.name
    try:
        result = sophia_monitor.check_backend_crash_log(log_path=fname, lines=10)
        # Musí vrátit poslední řádky a detekovat chybu
        assert 'last_lines' in result
        assert 'error_matches' in result
        # Musí najít ImportError a Traceback
        found_patterns = [pat for (_, _, pat) in result['error_matches']]
        assert any(re.match(r"ImportError", pat) for pat in found_patterns)
        assert any(re.match(r"Traceback", pat) for pat in found_patterns)
    finally:
        os.remove(fname)
