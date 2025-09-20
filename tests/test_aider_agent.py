
import pytest
import os
import tempfile
import shutil
from tests.conftest import robust_import, safe_remove

AiderAgent = robust_import('agents.aider_agent', 'AiderAgent')
SANDBOX_PATH = os.path.abspath('sandbox')


@pytest.fixture
def sandbox_snapshot(tmp_path):
    # Vytvoř snapshot sandboxu v temp adresáři
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    # Init git repo
    os.system(f"cd {sandbox_dir} && git init && git config user.email 'test@test.com' && git config user.name 'Test User' > /dev/null 2>&1")
    yield sandbox_dir
    # Cleanup přes safe_remove
    for fname in ["new_file.txt"]:
        fpath = sandbox_dir / fname
        try:
            safe_remove(str(fpath))
        except FileNotFoundError:
            pass



def test_aider_agent_init(request, sandbox_snapshot, snapshot):
    agent = AiderAgent()
    # Ověřujeme pouze na snapshotu, approval snapshot výstupu
    snapshot({
        "has_run_aider": hasattr(agent, "run_aider"),
        "has_propose_change": hasattr(agent, "propose_change"),
        "has_audit_change": hasattr(agent, "_audit_change"),
        "sandbox_path": str(agent.sandbox_path)
    })



def test_aider_agent_propose_change_mocked(request, sandbox_snapshot, monkeypatch, snapshot):
    # Mock the run_aider method to avoid actual subprocess calls
    def mock_run_aider(self, task):
        # Simulate aider making a change and creating a commit in snapshot
        os.system(
            f"cd {sandbox_snapshot} && touch new_file.txt && git add . && git commit -m 'feat: Add new file' > /dev/null 2>&1"
        )
        return {"status": "success", "message": "Change proposed."}

    monkeypatch.setattr(AiderAgent, "run_aider", mock_run_aider)
    monkeypatch.setattr(AiderAgent, "_audit_change", lambda self: None)

    agent = AiderAgent()
    result = agent.propose_change("Refactor the main loop.")
    # Approval snapshot výstupu
    snapshot(result)
    assert result["status"] == "success"
