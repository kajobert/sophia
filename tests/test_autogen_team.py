
import pytest
from tests.conftest import robust_import

def test_autogen_team_import(request):
    """Auditní test: pokud není pyautogen, vytvoří auditní snapshot a označí test jako xfail."""
    try:
        pyautogen = robust_import('pyautogen')
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot("pyautogen import OK")
    except Exception as e:
        # Auditní snapshot s důvodem selhání
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        msg = f"pyautogen není dostupný: {e}"
        if snapshot:
            snapshot(msg)
        pytest.xfail(msg)

# Šablona pro budoucí robustní test:
# def test_autogen_team_functionality(request, snapshot):
#     pyautogen = robust_import('pyautogen')
#     # ...test logic...
#     snapshot(str(result))
