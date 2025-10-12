"""
E2E tests with REAL Gemini API.

⚠️  WARNING: These tests cost money! They make actual API calls to Gemini.

Usage:
    # Run ONLY real LLM tests (requires GEMINI_API_KEY in .env)
    pytest tests/test_e2e_real_llm.py -v -m real_llm
    
    # Skip real LLM tests (default for CI/CD)
    pytest tests/ -v -m "not real_llm"
"""

import pytest
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.llm_manager import LLMManager
from core.plan_manager import PlanManager
from core.reflection_engine import ReflectionEngine
from core.nomad_orchestrator_v2 import NomadOrchestratorV2
from core.state_manager import State

# Load environment variables
load_dotenv()


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def check_api_key():
    """
    Zkontroluje že GEMINI_API_KEY je k dispozici.
    
    Pokud ne, testy budou skipped (ne failed).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip(
            "GEMINI_API_KEY not found in environment. "
            "Create .env file with your API key to run real LLM tests. "
            "See docs/REAL_LLM_SETUP.md for setup instructions."
        )
    return api_key


@pytest.fixture
async def llm_manager(check_api_key):
    """Fixture providing real LLMManager."""
    manager = LLMManager()
    yield manager
    # Cleanup if needed


@pytest.fixture
async def orchestrator(tmp_path, check_api_key):
    """Fixture providing NomadOrchestratorV2 with real LLM."""
    orch = NomadOrchestratorV2(project_root=str(tmp_path))
    await orch.initialize()
    yield orch
    await orch.shutdown()
    
    # Cleanup test files
    if orch.state_manager.session_file and os.path.exists(orch.state_manager.session_file):
        orch.state_manager.delete_session()


# ============================================================================
# BASIC CONNECTIVITY TESTS
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_gemini_basic_connectivity(llm_manager):
    """
    Test: Základní konektivita s Gemini API.
    
    Ověřuje:
    - API klíč funguje
    - Model odpovídá
    - Usage tracking funguje
    """
    model = llm_manager.get_llm("powerful")
    
    response, usage = await model.generate_content_async("Say exactly 'Hello'")
    
    # Assertions
    assert response is not None, "No response from Gemini"
    assert len(response) > 0, "Empty response"
    assert "hello" in response.lower(), f"Unexpected response: {response}"
    
    # Check usage tracking
    assert usage is not None, "No usage data"
    assert "usage" in usage, "Missing usage field"
    assert "total_tokens" in usage["usage"], "Missing total_tokens"
    assert usage["usage"]["total_tokens"] > 0, "Zero tokens reported"
    
    print(f"✅ Gemini connectivity OK")
    print(f"   Response: {response[:100]}")
    print(f"   Tokens: {usage['usage']['total_tokens']}")


@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_gemini_json_output(llm_manager):
    """
    Test: Gemini vrací platný JSON.
    
    Důležité pro plánování a reflection.
    """
    model = llm_manager.get_llm("powerful")
    
    prompt = """Return a JSON object with this exact structure:
```json
{
  "status": "ok",
  "value": 42
}
```

Return ONLY the JSON, nothing else."""
    
    response, _ = await model.generate_content_async(prompt)
    
    # Parse JSON
    import json, re
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try parsing whole response
        json_str = response.strip()
    
    data = json.loads(json_str)
    
    assert data["status"] == "ok"
    assert data["value"] == 42
    
    print(f"✅ JSON parsing OK")


# ============================================================================
# COMPONENT TESTS WITH REAL LLM
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_real_plan_generation(llm_manager, tmp_path):
    """
    Test: PlanManager vytvoří plán pomocí reálného LLM.
    """
    pm = PlanManager(llm_manager, project_root=str(tmp_path))
    
    # Simple task
    plan = await pm.create_plan(
        mission_goal="List all files in the sandbox/ directory",
        max_steps=5
    )
    
    # Assertions
    assert len(plan) > 0, "Empty plan generated"
    assert len(plan) <= 5, f"Too many steps: {len(plan)}"
    
    # Check plan structure
    for step in plan:
        assert step.id > 0, f"Invalid step ID: {step.id}"
        assert len(step.description) > 10, f"Too short description: {step.description}"
        assert step.status == "pending"
        assert step.estimated_tokens > 0
    
    # Check for logical flow
    step_ids = [s.id for s in plan]
    assert step_ids == sorted(step_ids), "Steps not in order"
    
    print(f"✅ Plan generated: {len(plan)} steps")
    for step in plan:
        print(f"   {step.id}. {step.description[:60]}")


@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_real_reflection_on_failure(llm_manager):
    """
    Test: ReflectionEngine analyzuje chybu pomocí reálného LLM.
    """
    re = ReflectionEngine(llm_manager)
    
    # Simulate a failed step
    failed_step = {
        "id": 1,
        "description": "Create file test.txt",
        "status": "failed"
    }
    
    error_msg = "FileNotFoundError: Directory 'nonexistent/' does not exist"
    
    result = await re.reflect_on_failure(
        failed_step=failed_step,
        error_message=error_msg,
        attempt_count=1
    )
    
    # Assertions
    assert result is not None
    assert result.analysis, "No analysis generated"
    assert result.root_cause, "No root cause identified"
    assert result.suggested_action in [
        "retry", "retry_modified", "replanning", "ask_user", "skip_step"
    ], f"Invalid action: {result.suggested_action}"
    assert 0 <= result.confidence <= 1, f"Invalid confidence: {result.confidence}"
    
    print(f"✅ Reflection completed")
    print(f"   Analysis: {result.analysis[:100]}")
    print(f"   Action: {result.suggested_action} (confidence: {result.confidence:.0%})")


# ============================================================================
# E2E MISSION TESTS
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
@pytest.mark.slow
async def test_simple_real_mission(orchestrator, tmp_path):
    """
    Test: Kompletní jednoduchá mise s reálným LLM.
    
    Mission: Vytvoř soubor hello.txt
    Expected: Plánování → Exekuce → Dokončení
    """
    # Create sandbox dir in tmp_path
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(exist_ok=True)
    
    test_file = sandbox / "hello.txt"
    
    # Start mission
    await orchestrator.start_mission(
        mission_goal=f"Create a file at {test_file} with content 'Hello from Nomad!'",
        recover_if_crashed=False
    )
    
    # Assertions
    final_state = orchestrator.state_manager.get_state()
    assert final_state in [State.COMPLETED, State.RESPONDING], \
        f"Mission not completed. State: {final_state.value}"
    
    # Check file was created
    assert test_file.exists(), "File was not created"
    
    content = test_file.read_text()
    assert "Hello" in content, f"Unexpected content: {content}"
    
    # Check budget tracking
    budget_summary = orchestrator.budget_tracker.get_summary()
    print(f"✅ Mission completed")
    print(f"   Budget: {budget_summary}")


@pytest.mark.real_llm
@pytest.mark.asyncio
@pytest.mark.slow
async def test_multi_step_real_mission(orchestrator, tmp_path):
    """
    Test: Více-krokový task s reálným LLM.
    
    Mission: List files → Count them → Report
    """
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(exist_ok=True)
    
    # Create some test files
    for i in range(3):
        (sandbox / f"test_{i}.txt").write_text(f"Test {i}")
    
    await orchestrator.start_mission(
        mission_goal=f"List all .txt files in {sandbox} and count how many there are",
        recover_if_crashed=False
    )
    
    # Assertions
    final_state = orchestrator.state_manager.get_state()
    assert final_state in [State.COMPLETED, State.RESPONDING], \
        f"Mission failed. State: {final_state.value}"
    
    # Check plan was created and executed
    plan_data = orchestrator.state_manager.get_data("plan")
    assert plan_data is not None, "No plan created"
    
    progress = orchestrator.plan_manager.get_progress()
    assert progress["completed"] > 0, "No steps completed"
    
    print(f"✅ Multi-step mission completed")
    print(f"   Steps completed: {progress['completed']}/{progress['total_steps']}")
    print(f"   Budget: {orchestrator.budget_tracker.get_summary()}")


@pytest.mark.real_llm
@pytest.mark.asyncio
@pytest.mark.slow
async def test_mission_with_error_recovery(orchestrator, tmp_path):
    """
    Test: Mise s chybou → Reflection → Recovery.
    
    Testuje celý error handling flow s reálným LLM.
    """
    # Task that will likely fail on first try
    await orchestrator.start_mission(
        mission_goal="Delete a file that doesn't exist: /nonexistent/fake.txt",
        recover_if_crashed=False
    )
    
    # Should complete (even if with skipped steps)
    final_state = orchestrator.state_manager.get_state()
    assert final_state != State.ERROR, "Mission ended in ERROR state"
    
    # Check reflection was used
    reflection_history = orchestrator.reflection_engine.reflection_history
    assert len(reflection_history) > 0, "No reflection performed"
    
    print(f"✅ Error recovery tested")
    print(f"   Reflections: {len(reflection_history)}")


# ============================================================================
# COST & PERFORMANCE TESTS
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_budget_tracking_with_real_llm(orchestrator, tmp_path):
    """
    Test: BudgetTracker správně sleduje real LLM usage.
    """
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(exist_ok=True)
    
    # Set low budget to test warnings
    orchestrator.budget_tracker.max_tokens = 10000
    
    await orchestrator.start_mission(
        mission_goal=f"Create file {sandbox}/budget_test.txt with content 'test'",
        recover_if_crashed=False
    )
    
    # Check tracking
    summary = orchestrator.budget_tracker.get_detailed_summary()
    
    assert summary["total_tokens"] > 0, "No tokens tracked"
    assert summary["total_cost"] > 0, "No cost calculated"
    assert len(summary["step_costs"]) > 0, "No step costs recorded"
    
    print(f"✅ Budget tracking verified")
    print(f"   Tokens: {summary['total_tokens']}")
    print(f"   Cost: ${summary['total_cost']:.4f}")
    print(f"   Steps tracked: {len(summary['step_costs'])}")


# ============================================================================
# SUMMARY
# ============================================================================

def pytest_configure(config):
    """Print info about real LLM tests."""
    if config.option.markexpr and "real_llm" in config.option.markexpr:
        print("\n" + "="*70)
        print("⚠️  REAL LLM TESTS ENABLED - THESE COST MONEY!")
        print("="*70)
        print("Running tests with actual Gemini API calls.")
        print("Estimated cost: ~$0.10 - $0.50 depending on test selection")
        print("="*70 + "\n")
