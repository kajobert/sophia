import pytest

@pytest.mark.skip(reason="ArchitectAgent nelze robustně izolovat bez mockování LLM/memori.")
def test_architect_agent_init():
    from agents.architect_agent import ArchitectAgent
    agent = ArchitectAgent()
    assert hasattr(agent, '__init__')
