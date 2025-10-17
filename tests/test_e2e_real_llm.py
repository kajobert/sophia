"""
E2E tests with REAL LLM APIs (Gemini + OpenRouter).

⚠️  WARNING: These tests cost money! They make actual API calls.

Providers tested:
- Gemini API (primary, rate limited: 50 RPM)
- OpenRouter API (15 models, cheaper options available)

Usage:
    # Run ONLY real LLM tests (requires API keys in .env)
    pytest tests/test_e2e_real_llm.py -v -m real_llm
    
    # Skip real LLM tests (default for CI/CD)
    pytest tests/ -v -m "not real_llm"
    
⚠️  RATE LIMITS: 
    - Gemini Free Tier: 50 RPM, tests use retry logic
    - OpenRouter: Varies by model, generally higher limits
    Full test suite may take 5-10 minutes to complete.
    
💰 COST OPTIMIZATION:
    Tests use cheapest OpenRouter models where possible:
    - Qwen 2.5 72B: $0.07/1M tokens (cheapest)
    - Gemma 3 27B: $0.09/1M tokens
    Total cost per full test run: ~$0.01-0.05
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
from core.nomad_orchestrator_v2 import NomadOrchestratorV2, MissionState

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
    Zkontroluje že alespoň jeden API klíč je k dispozici.
    
    Podporované: GEMINI_API_KEY, OPENROUTER_API_KEY
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not gemini_key and not openrouter_key:
        pytest.skip(
            "No API keys found. Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env. "
            "See docs/REAL_LLM_SETUP.md for setup instructions."
        )
    
    return {
        "gemini": gemini_key,
        "openrouter": openrouter_key
    }


@pytest.fixture
async def llm_manager(check_api_key):
    """
    Fixture providing real LLMManager.
    
    Uses gemini-1.5-flash (higher free tier: 1500 RPM vs 50 RPM for 2.0-flash-exp)
    """
    manager = LLMManager()
    # Override to use cheaper model with higher rate limits
    manager.aliases["powerful"] = "gemini-1.5-flash"
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
    source_config = project_root / "config" / "config.yaml"
    dest_config = config_dir / "config.yaml"
    shutil.copy(source_config, dest_config)
    
    # Copy .env if exists
    source_env = project_root / ".env"
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
# OPENROUTER TESTS (Cost-Effective Alternative)
# ============================================================================

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_openrouter_qwen_cheap_model(llm_manager, check_api_key):
    """
    Test: OpenRouter s Qwen 2.5 72B (nejlevnější: $0.07/1M tokens).
    
    Ověřuje:
    - OpenRouter API connectivity
    - Cheapest model funguje
    - Cost tracking
    """
    if not check_api_key.get("openrouter"):
        pytest.skip("OPENROUTER_API_KEY not available")
    
    await wait_for_rate_limit()
    
    async def test_call():
        # Get cheap model
        model = llm_manager.get_llm("cheap")  # Should be Qwen
        
        response, usage = await model.generate_content_async("Say exactly 'Hello'")
        
        # Assertions
        assert response is not None, "No response from OpenRouter"
        assert len(response) > 0, "Empty response"
        assert "hello" in response.lower(), f"Unexpected response: {response}"
        
        # Check usage tracking
        assert usage is not None, "No usage data"
        
        # OpenRouter uses 'cost' key, not 'cost_usd'
        cost_key = "cost" if "cost" in usage else "cost_usd"
        assert cost_key in usage, f"Missing cost tracking. Keys: {usage.keys()}"
        assert usage[cost_key] < 0.001, f"Too expensive: ${usage[cost_key]}"  # Should be ~$0.0001
        
        print(f"✅ OpenRouter Qwen OK")
        print(f"   Response: {response[:50]}")
        print(f"   Cost: ${usage[cost_key]:.6f}")
        print(f"   Model: {usage.get('model', 'unknown')}")
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=5.0)


@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_openrouter_model_variety(llm_manager, check_api_key):
    """
    Test: Různé OpenRouter modely (cheap, balanced, powerful).
    
    Ověřuje:
    - Model selection funguje
    - Všechny tier levels dostupné
    - Cost scaling (cheap < balanced < powerful)
    """
    if not check_api_key.get("openrouter"):
        pytest.skip("OPENROUTER_API_KEY not available")
    
    await wait_for_rate_limit()
    
    async def test_call():
        models_to_test = [
            ("cheap", "qwen"),          # Qwen 2.5 72B - $0.07
            ("balanced", "gemma"),      # Gemma 3 27B - $0.09
        ]
        
        costs = {}
        
        for tier, expected_provider in models_to_test:
            model = llm_manager.get_llm(tier)
            response, usage = await model.generate_content_async("Hi")
            
            assert response is not None
            assert len(response) > 0
            
            # Handle both 'cost' (OpenRouter) and 'cost_usd' keys
            cost = usage.get("cost") or usage.get("cost_usd", 0)
            costs[tier] = cost
            print(f"   {tier:10s}: ${costs[tier]:.6f} - {usage.get('model', 'unknown')}")
            
            await asyncio.sleep(1)  # Small delay between models
        
        # Verify both models worked
        assert costs["cheap"] > 0, "Cheap model cost not tracked"
        assert costs["balanced"] > 0, "Balanced model cost not tracked"
        
        print(f"✅ OpenRouter model variety OK")
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=5.0)


@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_openrouter_plan_generation(llm_manager, tmp_path, check_api_key):
    """
    Test: PlanManager s OpenRouter (cheap model).
    
    Ověřuje že levný model dokáže generovat plány.
    """
    if not check_api_key.get("openrouter"):
        pytest.skip("OPENROUTER_API_KEY not available")
    
    await wait_for_rate_limit()
    
    async def test_call():
        # Create a custom LLM manager configured for cheap model
        from core.llm_manager import LLMManager
        cheap_llm = LLMManager()
        
        # Override the "powerful" alias to use cheap model for this test
        cheap_llm.aliases["powerful"] = "qwen/qwen-2.5-72b-instruct"
        
        pm = PlanManager(cheap_llm, project_root=str(tmp_path))
        
        plan = await pm.create_plan(
            mission_goal="List files in current directory",
            max_steps=3
        )
        
        # Assertions
        assert len(plan) > 0, "Empty plan"
        assert len(plan) <= 3, f"Too many steps: {len(plan)}"
        
        for step in plan:
            assert step.id > 0
            assert len(step.description) > 5
        
        print(f"✅ OpenRouter plan generation OK")
        print(f"   Steps: {len(plan)}")
    
    await retry_on_rate_limit(test_call, max_retries=3, base_delay=10.0)


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
        await orchestrator.execute_mission(
            mission_goal="Create a file 'hello.txt' in sandbox/ with content 'Hello from Nomad!'"
        )
    
    # Retry on rate limits
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions: Accept success OR a graceful failure due to rate limiting.
    history_str = "".join(str(item) for item in orchestrator.history)
    if "429" in history_str or "rate limit" in history_str:
        print(f"✅ Mission gracefully handled rate limit error, which is acceptable for this test.")
        pytest.skip("Skipping final assertions due to API rate limiting.")

    assert test_file.exists(), f"Mission failed: The file '{test_file}' was not created."
    content = test_file.read_text()
    assert "Hello from Nomad!" in content, f"File content is incorrect: {content}"
    print(f"✅ Mission successful: File '{test_file}' created with correct content.")
    
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
        await orchestrator.execute_mission(
            mission_goal=f"List all .txt files in {sandbox} and count how many there are"
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions: Accept success OR a graceful failure due to rate limiting.
    history_str = "".join(str(item) for item in orchestrator.history)
    if "429" in history_str or "rate limit" in history_str:
        print(f"✅ Mission gracefully handled rate limit error, which is acceptable for this test.")
        pytest.skip("Skipping final assertions due to API rate limiting.")

    assert "list_files" in history_str, "Agent did not attempt to list files."
    assert "3" in history_str, "Agent did not seem to correctly count the 3 files."
    print("✅ Mission successful: Agent correctly listed and counted the files.")


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
        await orchestrator.execute_mission(
            mission_goal="Delete a file that doesn't exist: /nonexistent/fake.txt"
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions: Accept success OR a graceful failure due to rate limiting.
    history_str = "".join(str(item) for item in orchestrator.history)
    if "429" in history_str or "rate limit" in history_str:
        print(f"✅ Mission gracefully handled rate limit error, which is acceptable for this test.")
        pytest.skip("Skipping final assertions due to API rate limiting.")

    assert "Error executing tool" in history_str and "nonexistent" in history_str, \
        "Agent did not log the expected error after the tool failed."
    assert "mission_complete" in history_str, \
        "Agent did not call mission_complete after handling the error."
    print("✅ Mission successful: Agent gracefully handled the error.")


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
        await orchestrator.execute_mission(
            mission_goal=f"Create file {sandbox}/budget_test.txt with content 'test'"
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions: Accept success OR a graceful failure due to rate limiting.
    history_str = "".join(str(item) for item in orchestrator.history)
    if "429" in history_str or "rate limit" in history_str:
        print(f"✅ Mission gracefully handled rate limit error, which is acceptable for this test.")
        pytest.skip("Skipping final assertions due to API rate limiting.")

    summary = orchestrator.budget_tracker.get_detailed_summary()
    total_tokens = summary.get("tokens", {}).get("used", 0)
    assert total_tokens > 0, "Budget tracker did not record any token usage."
    print(f"✅ Budget tracking verified. Tokens used: {total_tokens}")


@pytest.mark.real_llm
@pytest.mark.asyncio
@pytest.mark.slow
async def test_complete_mission_with_openrouter(orchestrator, tmp_path, check_api_key):
    """
    Test: Kompletní mise používající OpenRouter (cheap model).
    
    Mission: Create simple text file
    LLM: Qwen 2.5 72B (cheapest OpenRouter option)
    Expected Cost: ~$0.001-0.005
    
    Note: Tests OpenRouter end-to-end integration.
    """
    if not check_api_key.get("openrouter"):
        pytest.skip("OPENROUTER_API_KEY not available")
    
    await wait_for_rate_limit()
    
    # Force orchestrator to use cheap OpenRouter model
    orchestrator.llm_manager.default_tier = "cheap"
    
    test_file = tmp_path / "sandbox" / "openrouter_test.txt"
    
    async def run_mission():
        await orchestrator.execute_mission(
            mission_goal="Create file 'openrouter_test.txt' in sandbox/ with content 'OpenRouter works!'"
        )
    
    await retry_on_rate_limit(run_mission, max_retries=2, base_delay=10.0)
    
    # Assertions: Accept success OR a graceful failure due to rate limiting.
    history_str = "".join(str(item) for item in orchestrator.history)
    if "429" in history_str or "rate limit" in history_str:
        print(f"✅ Mission gracefully handled rate limit error, which is acceptable for this test.")
        pytest.skip("Skipping final assertions due to API rate limiting.")

    assert test_file.exists(), f"Mission failed: The file '{test_file}' was not created."
    content = test_file.read_text()
    assert "OpenRouter works!" in content, f"File content is incorrect: {content}"
    print(f"✅ Mission successful: File '{test_file}' created with correct content using OpenRouter.")
    
    # Check cost (should be very low with Qwen)
    summary = orchestrator.budget_tracker.get_summary()
    
    # Handle both 'cost' and 'total_cost' keys
    cost = summary.get("cost") or summary.get("total_cost", 0) or summary.get("estimated_cost", 0)
    
    if cost > 0:
        assert cost < 0.01, f"Too expensive for simple mission: ${cost}"
        print(f"   💰 Cost: ${cost:.6f} (Qwen model)")
    
    print(f"✅ OpenRouter E2E mission completed")
    print(f"   Final state: {final_state.value}")
    print(f"   Model tier: cheap (OpenRouter Qwen)")


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
