import pytest
from agents.aider_agent import AiderAgent

def test_aider_agent_init():
    agent = AiderAgent()
    assert hasattr(agent, 'run_aider')
    assert hasattr(agent, 'propose_change')
    assert hasattr(agent, '_audit_change')
