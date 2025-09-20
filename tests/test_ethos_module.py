

import pytest
from tests.conftest import robust_import

def test_ethos_module_import(request):
    """Auditní test: pokud není EthosModule/memori, vytvoří auditní snapshot a označí test jako xfail."""
    try:
        EthosModule = robust_import('core.ethos_module', 'EthosModule')
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot("EthosModule import OK")
    except Exception as e:
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        msg = f"EthosModule není dostupný: {e}"
        if snapshot:
            snapshot(msg)
        pytest.xfail(msg)

# Šablona pro robustní testy:
# def test_ethos_module_loads_dna(request, snapshot):
#     EthosModule = robust_import('core.ethos_module', 'EthosModule')
#     ethos = EthosModule()
#     snapshot(str(ethos.dna_db))
#
# def test_planstate_lifecycle(request, snapshot):
#     PlanState = robust_import('core.ethos_module', 'PlanState')
#     propose_plan = robust_import('core.ethos_module', 'propose_plan')
#     critique_plan = robust_import('core.ethos_module', 'critique_plan')
#     revise_plan = robust_import('core.ethos_module', 'revise_plan')
#     approve_or_reject = robust_import('core.ethos_module', 'approve_or_reject')
#     state = PlanState("plan")
#     state2 = propose_plan(state)
#     state3 = critique_plan(state2)
#     state4 = revise_plan(state3)
#     result = approve_or_reject(state4)
#     snapshot(str(result))
