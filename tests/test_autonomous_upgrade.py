import pytest
import os
import subprocess
import sys
from unittest.mock import patch, MagicMock

# Přidání cesty k `core` a `agents` modulům
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.consciousness_loop import orchestrate_self_improvement

# Cesta k sandboxu, který budeme používat v testech
SANDBOX_PATH = os.path.abspath("./sandbox")

@pytest.fixture(autouse=True)
def setup_sandbox():
    """
    Fixture to ensure the sandbox is clean before each test
    and that it's a git repository.
    """
    # Ujistíme se, že sandbox existuje a je prázdný
    if os.path.exists(SANDBOX_PATH):
        # Důkladné vyčištění, pokud by tam něco zbylo
        subprocess.run(f"rm -rf {SANDBOX_PATH}", shell=True, check=True)
    os.makedirs(SANDBOX_PATH, exist_ok=True)

    # Inicializace Gitu v sandboxu
    subprocess.run(["git", "init"], cwd=SANDBOX_PATH, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=SANDBOX_PATH, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=SANDBOX_PATH, check=True)
    # Vytvoření počátečního committu, aby `git reset HEAD` fungoval
    subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd=SANDBOX_PATH, check=True, capture_output=True)

    yield

    # Úklid po testu
    subprocess.run(f"rm -rf {SANDBOX_PATH}", shell=True, check=True)


# Patchujeme tam, kde je objekt *použit* (v `aider_agent`), ne tam, kde je definován.
@patch('agents.aider_agent.EthicalReviewTool')
@patch('agents.aider_agent.AiderAgent.run_aider')
def test_autonomous_upgrade_e2e_success(mock_run_aider, mock_EthicalReviewTool):
    """
    E2E test, který ověřuje úspěšný průběh autonomního vylepšení.
    Mockuje `aider` proces a celou třídu `EthicalReviewTool`.
    """
    # --- Fáze 1: Nastavení mocků ---

    # Nastavení mocku pro EthicalReviewTool
    # Když se v kódu zavolá `EthicalReviewTool()`, vrátí se instance mocku.
    # Na této instanci nastavíme návratovou hodnotu metody `_run`.
    mock_instance = mock_EthicalReviewTool.return_value
    mock_instance._run.return_value = "Ethical Review Feedback: Looks good. (Decision: Pass)"

    # Nastavení mocku pro Aider
    def side_effect(*args, **kwargs):
        version_path = os.path.join(SANDBOX_PATH, "VERSION")
        utils_path = os.path.join(SANDBOX_PATH, "utils.py")
        with open(version_path, "w") as f:
            f.write("1.0.0")
        with open(utils_path, "w") as f:
            f.write("def get_project_version():\n")
            f.write("    with open('VERSION', 'r') as f:\n")
            f.write("        return f.read().strip()\n")
        return {"status": "success", "files_changed": ["VERSION", "utils.py"]}

    mock_run_aider.side_effect = side_effect

    # --- Fáze 2: Spuštění testované funkce ---
    success = orchestrate_self_improvement()

    # --- Fáze 3: Ověření výsledků ---
    assert success is True
    mock_run_aider.assert_called_once()
    mock_EthicalReviewTool.assert_called_once() # Ověří, že byla třída instancována
    mock_instance._run.assert_called_once() # Ověří, že na instanci byla zavolána metoda _run

    version_path = os.path.join(SANDBOX_PATH, "VERSION")
    utils_path = os.path.join(SANDBOX_PATH, "utils.py")
    assert os.path.exists(version_path)
    assert os.path.exists(utils_path)
    with open(version_path, "r") as f:
        assert f.read() == "1.0.0"

    import importlib.util
    spec = importlib.util.spec_from_file_location("sandbox_utils", utils_path)
    sandbox_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sandbox_utils)

    original_cwd = os.getcwd()
    os.chdir(SANDBOX_PATH)
    try:
        assert sandbox_utils.get_project_version() == "1.0.0"
    finally:
        os.chdir(original_cwd)

    git_log = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=SANDBOX_PATH,
        capture_output=True,
        text=True,
        check=True
    )
    assert "Autonomously generated change" in git_log.stdout
