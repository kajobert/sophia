import pytest
import os
from agents.aider_agent import AiderAgent, SANDBOX_PATH

@pytest.fixture(scope="module")
def setup_sandbox():
    """Set up a clean sandbox directory for aider tests."""
    if not os.path.exists(SANDBOX_PATH):
        os.makedirs(SANDBOX_PATH)
    # Create a dummy git repo in sandbox for audit testing
    if not os.path.exists(os.path.join(SANDBOX_PATH, '.git')):
        os.system(f"cd {SANDBOX_PATH} && git init && git config user.email 'test@test.com' && git config user.name 'Test User' > /dev/null 2>&1")
    yield

def test_aider_agent_init(setup_sandbox):
    agent = AiderAgent()
    assert agent.sandbox_path.endswith("/sandbox")
    assert hasattr(agent, 'run_aider')
    assert hasattr(agent, 'propose_change')
    assert hasattr(agent, '_audit_change')

def test_aider_agent_propose_change_mocked(setup_sandbox, monkeypatch):
    # Mock the run_aider method to avoid actual subprocess calls
    def mock_run_aider(self, task):
        # Simulate aider making a change and creating a commit
        os.system(f"cd {SANDBOX_PATH} && touch new_file.txt && git add . && git commit -m 'feat: Add new file' > /dev/null 2>&1")
        return {"status": "success", "message": "Change proposed."}

    monkeypatch.setattr(AiderAgent, "run_aider", mock_run_aider)

    # Also mock the _audit_change to prevent DB connection via EthosModule
    monkeypatch.setattr(AiderAgent, "_audit_change", lambda self: None)

    agent = AiderAgent()
    result = agent.propose_change("Refactor the main loop.")
    assert result['status'] == 'success'
