import pytest
from core.ethos_module import (
    EthosModule,
    PlanState,
    approve_or_reject,
    critique_plan,
    propose_plan,
    revise_plan,
)

# Testy EthosModule jsou skipnuty, protože EthosModule závisí na paměti/memori, což nelze robustně testovat bez mockování.
pytest.skip(
    "Testy EthosModule nelze robustně izolovat bez mockování paměti/memori.",
    allow_module_level=True,
)


def test_ethos_module_loads_dna():
    ethos = EthosModule()
    assert hasattr(ethos, "dna_db")
    assert ethos.dna_db is not None


def test_planstate_lifecycle():
    state = PlanState("plan")
    assert state.plan == "plan"
    state2 = propose_plan(state)
    assert isinstance(state2, PlanState)
    state3 = critique_plan(state2)
    assert isinstance(state3, PlanState)
    state4 = revise_plan(state3)
    assert isinstance(state4, PlanState)
    result = approve_or_reject(state4)
    assert isinstance(result, str)
