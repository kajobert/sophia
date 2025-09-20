import pytest
from tests.conftest import robust_import

@pytest.mark.skip(reason="ArchitectAgent nelze robustně izolovat bez mockování LLM/memori.")
def test_architect_agent_init(request, snapshot):
    ArchitectAgent = robust_import('agents.architect_agent', 'ArchitectAgent')
    agent = ArchitectAgent()
    assert hasattr(agent, "__init__")
    snapshot(str(agent))
