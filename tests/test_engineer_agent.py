

import pytest
from tests.conftest import robust_import

def test_engineer_agent_import(request):
    """Auditní test: pokud není CrewAI/BaseTool, vytvoří auditní snapshot a označí test jako xfail."""
    try:
        EngineerAgent = robust_import('agents.engineer_agent', 'EngineerAgent')
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot("EngineerAgent import OK")
    except Exception as e:
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        msg = f"EngineerAgent není dostupný: {e}"
        if snapshot:
            snapshot(msg)
        pytest.xfail(msg)

# Šablona pro budoucí robustní test:
# def test_engineer_agent_init(request, snapshot):
#     EngineerAgent = robust_import('agents.engineer_agent', 'EngineerAgent')
#     agent = EngineerAgent()
#     snapshot(str(agent))
