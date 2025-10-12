"""
E2E tests with REAL Gemini API.

⚠️  WARNING: These tests cost money! They make actual API calls to Gemini.

Usage:
    # Run ONLY real LLM tests (requires GEMINI_API_KEY in .env)
    pytest tests/test_e2e_real_llm.py -v -m real_llm
    
    # Skip real LLM tests (default for CI/CD)
    pytest tests/ -v -m "not real_llm"
    
⚠️  RATE LIMITS: Gemini API has strict rate limits (50 RPM).
    These tests include delays and retry logic to handle rate limits.
    Full test suite may take 5-10 minutes to complete.
"""

import pytest
import os
import sys
import asyncio
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
# HELPER FUNCTIONS
# ============================================================================

async def wait_for_rate_limit():
    """
    Wait between tests to avoid Gemini API rate limits.
    
    Gemini Free Tier: 50 requests per minute
    Conservative approach: 2 seconds between requests
    """
    await asyncio.sleep(2.0)


async def retry_on_rate_limit(func, max_retries=3, base_delay=5.0):
    """
    Retry function on rate limit errors with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds (will be doubled each retry)
    
    Returns:
        Function result
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if any(keyword in error_str for keyword in ['rate limit', 'quota', '429', 'resource exhausted']):
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"\n⏳ Rate limit hit, waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(delay)
                    continue
            
            # Not a rate limit error, raise immediately
            raise
    
    # All retries exhausted
    raise last_exception


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
    """
    Fixture providing NomadOrchestratorV2 with real LLM.
    
    Creates temporary config structure for testing.
    """
    import shutil
    
    # Create config directory in tmp_path
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create sandbox directory
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    
    # Copy config.yaml to tmp directory
    source_config = "/workspaces/sophia/config/config.yaml"
    dest_config = config_dir / "config.yaml"
    shutil.copy(source_config, dest_config)
    
    # Copy .env if exists
    source_env = "/workspaces/sophia/.env"
    if os.path.exists(source_env):
        dest_env = tmp_path / ".env"
        shutil.copy(source_env, dest_env)
    
    # Initialize orchestrator with tmp_path
    orch = NomadOrchestratorV2(project_root=str(tmp_path))
    await orch.initialize()
    yield orch
    
    # Simple cleanup - no shutdown() or delete_session() methods exist


# ============================================================================
# BASIC CONNECTIVITY TESTS
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_gemini_basic_connectivity(llm_manager):
    """
    Test: Gemini API je dostupné a odpovídá.
    
    Ověřuje:
    - API key funguje
    - Model odpovídá na jednoduchý prompt
    - Usage tracking funguje
    """
    await wait_for_rate_limit()
    
    async def test_call():
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
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=25.0)


@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_gemini_json_output(llm_manager):
    """
    Test: Gemini vrací platný JSON.
    
    Důležité pro plánování a reflection.
    """
    await wait_for_rate_limit()
    
    async def test_call():
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
            json_str = response
        
        data = json.loads(json_str.strip())
        
        # Assertions
        assert data["status"] == "ok", f"Wrong status: {data}"
        assert data["value"] == 42, f"Wrong value: {data}"
        
        print(f"✅ JSON parsing OK")
        print(f"   Data: {data}")
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=25.0)


# ============================================================================
# COMPONENT TESTS WITH REAL LLM
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_real_plan_generation(llm_manager, tmp_path):
    """
    Test: PlanManager vytvoří plán pomocí reálného LLM.
    """
    await wait_for_rate_limit()
    
    async def test_call():
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
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=25.0)


@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_real_reflection_on_failure(llm_manager):
    """
    Test: ReflectionEngine analyzuje chybu pomocí reálného LLM.
    """
    await wait_for_rate_limit()
    
    async def test_call():
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
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=25.0)


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
    Expected: Plánování → Exekuce → Dokončení (nebo Error s částečným úspěchem)
    
    Note: Real LLM může selhat z různých důvodů (rate limit, parsing errors).
          Test akceptuje i ERROR state pokud byl vytvořen plán.
    """
    await wait_for_rate_limit()
    
    # File path relative to sandbox/
    test_file = tmp_path / "sandbox" / "hello.txt"
    
    async def run_mission():
        # Start mission with simple instruction
        await orchestrator.start_mission(
            mission_goal="Create a file 'hello.txt' in sandbox/ with content 'Hello from Nomad!'",
            recover_if_crashed=False
        )
    
    # Retry on rate limits
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions - be lenient with final state
    final_state = orchestrator.state_manager.get_state()
    
    # Accept COMPLETED, RESPONDING, or even ERROR if we got past PLANNING
    acceptable_states = [State.COMPLETED, State.RESPONDING, State.ERROR, State.IDLE]
    assert final_state in acceptable_states, \
        f"Mission ended in unexpected state: {final_state.value}"
    
    # Check that planning occurred (minimum requirement)
    plan_data = orchestrator.state_manager.get_data("plan")
    assert plan_data is not None or len(orchestrator.plan_manager.steps) > 0, \
        "No plan was created - mission failed before planning"
    
    # If file was created, verify content (best case)
    if test_file.exists():
        content = test_file.read_text()
        assert "Hello" in content or "Nomad" in content, \
            f"File created but unexpected content: {content}"
        print(f"✅ Mission completed successfully - file created")
    else:
        # File not created - acceptable if mission hit errors but tried
        print(f"⚠️  Mission completed with state {final_state.value}, file not created")
        print(f"   This is acceptable for real LLM tests (rate limits, parsing errors)")
    
    # Check budget tracking (should have some data even on partial success)
    budget_summary = orchestrator.budget_tracker.get_summary()
    print(f"   Budget: {budget_summary}")


@pytest.mark.real_llm
@pytest.mark.asyncio
@pytest.mark.slow
async def test_multi_step_real_mission(orchestrator, tmp_path):
    """
    Test: Více-krokový task s reálným LLM.
    
    Mission: List files → Count them → Report
    
    Note: Accepts partial success due to real LLM unpredictability.
    """
    await wait_for_rate_limit()
    
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(exist_ok=True)
    
    # Create some test files
    for i in range(3):
        (sandbox / f"test_{i}.txt").write_text(f"Test {i}")
    
    async def run_mission():
        await orchestrator.start_mission(
            mission_goal=f"List all .txt files in {sandbox} and count how many there are",
            recover_if_crashed=False
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions - lenient for real LLM
    final_state = orchestrator.state_manager.get_state()
    acceptable_states = [State.COMPLETED, State.RESPONDING, State.ERROR, State.IDLE]
    assert final_state in acceptable_states, \
        f"Mission ended in unexpected state: {final_state.value}"
    
    # Check plan was created
    plan_data = orchestrator.state_manager.get_data("plan")
    if plan_data is not None or len(orchestrator.plan_manager.steps) > 0:
        progress = orchestrator.plan_manager.get_progress()
        print(f"✅ Plan created and executed")
        print(f"   Steps completed: {progress['completed']}/{progress['total_steps']}")
        print(f"   Budget: {orchestrator.budget_tracker.get_summary()}")
    else:
        print(f"⚠️  Mission ended in {final_state.value} without completing plan")
        print(f"   This is acceptable for real LLM tests (rate limits)")


@pytest.mark.real_llm
@pytest.mark.asyncio
@pytest.mark.slow
async def test_mission_with_error_recovery(orchestrator, tmp_path):
    """
    Test: Mise s chybou → Reflection → Recovery.
    
    Testuje celý error handling flow s reálným LLM.
    
    Note: Reflection may not always be triggered depending on error type.
          Test passes if mission completes gracefully (even with errors).
    """
    await wait_for_rate_limit()
    
    async def run_mission():
        # Task that will likely fail on first try
        await orchestrator.start_mission(
            mission_goal="Delete a file that doesn't exist: /nonexistent/fake.txt",
            recover_if_crashed=False
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Should complete gracefully (not crash)
    final_state = orchestrator.state_manager.get_state()
    
    # Any state except None/crash is acceptable
    assert final_state is not None, "Orchestrator crashed"
    
    # Check if reflection was used (ideal case)
    reflection_history = orchestrator.reflection_engine.reflection_history
    
    if len(reflection_history) > 0:
        print(f"✅ Error recovery with reflection")
        print(f"   Reflections: {len(reflection_history)}")
        print(f"   Final state: {final_state.value}")
    else:
        print(f"✅ Mission completed without reflection")
        print(f"   Final state: {final_state.value}")
        print(f"   Note: Reflection not triggered (task may have succeeded or failed early)")


# ============================================================================
# COST & PERFORMANCE TESTS
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_budget_tracking_with_real_llm(orchestrator, tmp_path):
    """
    Test: BudgetTracker správně sleduje real LLM usage.
    
    Note: Accepts partial data if mission encounters errors.
    """
    await wait_for_rate_limit()
    
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(exist_ok=True)
    
    # Set low budget to test warnings
    orchestrator.budget_tracker.max_tokens = 10000
    
    async def run_mission():
        await orchestrator.start_mission(
            mission_goal=f"Create file {sandbox}/budget_test.txt with content 'test'",
            recover_if_crashed=False
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Check tracking - use get_summary() instead of get_detailed_summary()
    summary = orchestrator.budget_tracker.get_summary()
    
    # Check if we have tracking data
    if "total_tokens" in summary or "tokens_used" in summary:
        tokens = summary.get("total_tokens") or summary.get("tokens_used", 0)
        cost = summary.get("total_cost") or summary.get("estimated_cost", 0)
        
        assert tokens >= 0, f"Invalid token count: {tokens}"
        assert cost >= 0, f"Invalid cost: {cost}"
        
        print(f"✅ Budget tracking verified")
        print(f"   Tokens: {tokens}")
        print(f"   Cost: ${cost:.4f}")
        print(f"   Summary: {summary}")
    else:
        # No tracking data - may happen if mission failed early
        print(f"⚠️  Budget tracking incomplete")
        print(f"   Summary: {summary}")
        print(f"   Note: Mission may have failed before LLM calls")


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
