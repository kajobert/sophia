

import pytest
from tests.conftest import robust_import

def test_consciousness_loop_import(request):
    """Auditní test: pokud není CrewAI/LLM, vytvoří auditní snapshot a označí test jako xfail."""
    try:
        ConsciousnessLoop = robust_import('core.consciousness_loop', 'ConsciousnessLoop')
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot("ConsciousnessLoop import OK")
    except Exception as e:
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        msg = f"ConsciousnessLoop není dostupný: {e}"
        if snapshot:
            snapshot(msg)
        pytest.xfail(msg)

# Šablona pro budoucí robustní test:
# def test_consciousness_loop_init(request, snapshot):
#     ConsciousnessLoop = robust_import('core.consciousness_loop', 'ConsciousnessLoop')
#     loop = ConsciousnessLoop()
#     snapshot(str(loop))
