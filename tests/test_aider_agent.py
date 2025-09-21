import pytest
import os
import git
from pathlib import Path
from agents.aider_agent import AiderAgent, SANDBOX_PATH


@pytest.fixture(scope="module")
def setup_sandbox():
    """Set up a clean sandbox directory for aider tests."""
    sandbox_path = Path(SANDBOX_PATH)
    sandbox_path.mkdir(exist_ok=True)

    # Create a dummy git repo in sandbox for audit testing
    if not (sandbox_path / ".git").exists():
        repo = git.Repo.init(sandbox_path)
        with repo.config_writer() as cw:
            cw.set_value("user", "email", "test@test.com")
            cw.set_value("user", "name", "Test User")
    yield


def test_aider_agent_init(setup_sandbox):
    agent = AiderAgent()
    assert agent.sandbox_path.endswith("/sandbox")
    assert hasattr(agent, "run_aider")
    assert hasattr(agent, "propose_change")
    assert hasattr(agent, "_audit_change")


def test_aider_agent_propose_change_mocked(setup_sandbox, monkeypatch):
    # Mock the run_aider method to avoid actual subprocess calls
    def mock_run_aider(self, task):
        # Simulate aider making a change and creating a commit safely
        repo = git.Repo(SANDBOX_PATH)
        (Path(SANDBOX_PATH) / "new_file.txt").touch()
        repo.index.add(["new_file.txt"])
        repo.index.commit("feat: Add new file")
        return {"status": "success", "message": "Change proposed."}

    monkeypatch.setattr(AiderAgent, "run_aider", mock_run_aider)

    # Also mock the _audit_change to prevent DB connection via EthosModule
    monkeypatch.setattr(AiderAgent, "_audit_change", lambda self: None)

    agent = AiderAgent()
    result = agent.propose_change("Refactor the main loop.")
    assert result["status"] == "success"
