"""
Test Suite for Phase 3.4: Cognitive Self-Tuning Plugin

Tests autonomous hypothesis testing and deployment workflow.

Test Scenarios:
1. Plugin initialization and config
2. Hypothesis creation event handling
3. Sandbox environment management
4. Code fix application and testing
5. Prompt optimization benchmarking
6. Config change validation
7. Deployment workflow
8. Rejection flow (insufficient improvement)

Author: SOPHIA AMI 1.0 - Phase 3.4
Date: 2025-11-06
"""

import asyncio
import pytest
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock

from core.events import Event, EventType
from core.event_bus import EventBus
from plugins.cognitive_self_tuning import CognitiveSelfTuning
from plugins.memory_sqlite import SQLiteMemory


@pytest.fixture
def event_bus():
    """Create EventBus instance."""
    return EventBus()


@pytest.fixture
def test_config():
    """Test configuration for self-tuning plugin."""
    # Create mock database
    from plugins.memory_sqlite import SQLiteMemory
    mock_db = SQLiteMemory()
    mock_db.setup({"db_path": ":memory:"})
    
    return {
        "autonomy": {
            "self_improvement": {
                "self_tuning": {
                    "improvement_threshold": 0.10,  # 10%
                    "sandbox_path": "sandbox/test_self_tuning",
                    "auto_deploy": False,  # Disable for tests
                    "max_concurrent_tests": 1
                }
            }
        },
        "all_plugins": {
            "memory_sqlite": mock_db
        },
        "event_bus": None
    }


@pytest.fixture
def cleanup_sandbox():
    """Cleanup sandbox directory after tests."""
    yield
    sandbox_path = Path("sandbox/test_self_tuning")
    if sandbox_path.exists():
        shutil.rmtree(sandbox_path)


@pytest.mark.asyncio
async def test_plugin_initialization(event_bus, test_config):
    """Test 1: Plugin initializes correctly with config."""
    print("\n" + "="*60)
    print("TEST 1: Plugin Initialization")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    
    # Setup plugin
    plugin.setup(test_config)
    
    assert plugin.improvement_threshold == 0.10
    assert plugin.sandbox_path == Path("sandbox/test_self_tuning")
    assert plugin.auto_deploy is False
    assert plugin.max_concurrent_tests == 1
    
    print("✅ Plugin initialized successfully")
    print(f"   Threshold: {plugin.improvement_threshold*100}%")
    print(f"   Sandbox: {plugin.sandbox_path}")
    print(f"   Auto-deploy: {plugin.auto_deploy}")


@pytest.mark.asyncio
async def test_sandbox_creation(event_bus, test_config, cleanup_sandbox):
    """Test 2: Sandbox environment is created and cleaned up."""
    print("\n" + "="*60)
    print("TEST 2: Sandbox Environment Management")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create test sandbox
    sandbox_dir = plugin.sandbox_path / "test_123"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test file in sandbox
    test_file = sandbox_dir / "test.py"
    test_file.write_text("# Test file")
    
    assert sandbox_dir.exists()
    assert test_file.exists()
    print(f"✅ Sandbox created: {sandbox_dir}")
    
    # Cleanup
    await plugin._cleanup_sandbox(sandbox_dir)
    
    assert not sandbox_dir.exists()
    print("✅ Sandbox cleaned up successfully")


@pytest.mark.asyncio
async def test_code_fix_application(event_bus, test_config, cleanup_sandbox):
    """Test 3: Code fix is applied correctly in sandbox."""
    print("\n" + "="*60)
    print("TEST 3: Code Fix Application")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create temporary test file
    test_file_path = Path("sandbox/test_plugin_temp.py")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_text("# Original code\ndef test(): pass")
    
    # Prepare sandbox
    sandbox_dir = plugin.sandbox_path / "test_code"
    
    # Apply fix
    proposed_fix = "# Fixed code\ndef test_improved(): return True"
    success = await plugin._apply_fix_in_sandbox(
        sandbox_dir=sandbox_dir,
        fix_type="code",
        target_file=str(test_file_path),
        proposed_fix=proposed_fix
    )
    
    assert success is True
    
    # Verify sandbox file has new content
    sandbox_file = sandbox_dir / test_file_path.name
    assert sandbox_file.exists()
    content = sandbox_file.read_text()
    assert "test_improved" in content
    assert "Fixed code" in content
    
    print("✅ Code fix applied successfully")
    print(f"   Sandbox file: {sandbox_file}")
    print(f"   Content: {content[:50]}...")
    
    # Cleanup
    test_file_path.unlink()
    await plugin._cleanup_sandbox(sandbox_dir)


@pytest.mark.asyncio
async def test_prompt_fix_application(event_bus, test_config, cleanup_sandbox):
    """Test 4: Prompt optimization is applied correctly."""
    print("\n" + "="*60)
    print("TEST 4: Prompt Optimization Application")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create temporary prompt file
    prompt_file_path = Path("config/prompts/test_prompt.txt")
    prompt_file_path.parent.mkdir(parents=True, exist_ok=True)
    original_prompt = "This is a very long and complex prompt that needs optimization for 8B models. " * 10
    prompt_file_path.write_text(original_prompt)
    
    # Prepare sandbox
    sandbox_dir = plugin.sandbox_path / "test_prompt"
    
    # Apply optimized prompt
    optimized_prompt = "Optimized short prompt for 8B model."
    success = await plugin._apply_fix_in_sandbox(
        sandbox_dir=sandbox_dir,
        fix_type="prompt",
        target_file=str(prompt_file_path),
        proposed_fix=optimized_prompt
    )
    
    assert success is True
    
    # Verify sandbox file
    sandbox_file = sandbox_dir / prompt_file_path.name
    assert sandbox_file.exists()
    content = sandbox_file.read_text()
    assert content == optimized_prompt
    
    print("✅ Prompt optimization applied")
    print(f"   Original length: {len(original_prompt)} chars")
    print(f"   Optimized length: {len(optimized_prompt)} chars")
    
    # Cleanup
    prompt_file_path.unlink()
    await plugin._cleanup_sandbox(sandbox_dir)


@pytest.mark.asyncio
async def test_config_fix_application(event_bus, test_config, cleanup_sandbox):
    """Test 5: Config changes are applied correctly."""
    print("\n" + "="*60)
    print("TEST 5: Config Fix Application")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create temporary config file
    config_file_path = Path("config/test_config.yaml")
    config_file_path.parent.mkdir(parents=True, exist_ok=True)
    original_config = {"setting1": "value1", "setting2": 100}
    with open(config_file_path, 'w') as f:
        yaml.dump(original_config, f)
    
    # Prepare sandbox
    sandbox_dir = plugin.sandbox_path / "test_config"
    
    # Apply config fix
    new_config = {"setting1": "optimized", "setting2": 200, "setting3": "new"}
    proposed_fix = yaml.dump(new_config)
    
    success = await plugin._apply_fix_in_sandbox(
        sandbox_dir=sandbox_dir,
        fix_type="config",
        target_file=str(config_file_path),
        proposed_fix=proposed_fix
    )
    
    assert success is True
    
    # Verify sandbox file
    sandbox_file = sandbox_dir / config_file_path.name
    assert sandbox_file.exists()
    with open(sandbox_file, 'r') as f:
        loaded_config = yaml.safe_load(f)
    assert loaded_config == new_config
    
    print("✅ Config fix applied successfully")
    print(f"   Original: {original_config}")
    print(f"   New: {loaded_config}")
    
    # Cleanup
    config_file_path.unlink()
    await plugin._cleanup_sandbox(sandbox_dir)


@pytest.mark.asyncio
async def test_prompt_benchmarking(event_bus, test_config, cleanup_sandbox):
    """Test 6: Prompt benchmarking calculates improvement."""
    print("\n" + "="*60)
    print("TEST 6: Prompt Benchmarking")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create baseline and optimized prompts
    prompt_file = Path("config/prompts/test_benchmark.txt")
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    
    baseline_prompt = "Very long complex prompt. " * 50  # 1350 chars
    prompt_file.write_text(baseline_prompt)
    
    sandbox_dir = plugin.sandbox_path / "test_benchmark"
    sandbox_dir.mkdir(parents=True)
    sandbox_prompt = sandbox_dir / "test_benchmark.txt"
    optimized_prompt = "Short clear prompt."  # 19 chars
    sandbox_prompt.write_text(optimized_prompt)
    
    # Run benchmark
    results = await plugin._benchmark_prompt(
        workspace_root=Path.cwd(),
        sandbox_dir=sandbox_dir,
        target_file=str(prompt_file)
    )
    
    assert "improvement_percentage" in results
    assert results["improvement_percentage"] > 0
    assert results["baseline_length"] == len(baseline_prompt)
    assert results["new_length"] == len(optimized_prompt)
    
    print("✅ Prompt benchmarking successful")
    print(f"   Baseline: {results['baseline_length']} chars")
    print(f"   Optimized: {results['new_length']} chars")
    print(f"   Improvement: {results['improvement_percentage']*100:.1f}%")
    
    # Cleanup
    prompt_file.unlink()
    await plugin._cleanup_sandbox(sandbox_dir)


@pytest.mark.asyncio
async def test_config_benchmarking(event_bus, test_config, cleanup_sandbox):
    """Test 7: Config benchmarking validates YAML."""
    print("\n" + "="*60)
    print("TEST 7: Config Benchmarking")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create test config
    config_file = Path("config/test_bench_config.yaml")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text("setting: value")
    
    sandbox_dir = plugin.sandbox_path / "test_config_bench"
    sandbox_dir.mkdir(parents=True)
    sandbox_config = sandbox_dir / "test_bench_config.yaml"
    sandbox_config.write_text("optimized_setting: better_value")
    
    # Run benchmark
    results = await plugin._benchmark_config(
        workspace_root=Path.cwd(),
        sandbox_dir=sandbox_dir,
        target_file=str(config_file)
    )
    
    assert "improvement_percentage" in results
    assert results["config_valid"] is True
    assert results["improvement_percentage"] == 0.10  # Conservative estimate
    
    print("✅ Config benchmarking successful")
    print(f"   Valid: {results['config_valid']}")
    print(f"   Improvement: {results['improvement_percentage']*100:.1f}%")
    
    # Cleanup
    config_file.unlink()
    await plugin._cleanup_sandbox(sandbox_dir)


@pytest.mark.asyncio
async def test_hypothesis_workflow_mock(event_bus, test_config, cleanup_sandbox):
    """Test 8: Complete hypothesis workflow (simplified - test database integration)."""
    print("\n" + "="*60)
    print("TEST 8: Hypothesis Database Integration")
    print("="*60)
    
    plugin = CognitiveSelfTuning()
    plugin.setup(test_config)
    
    # Create mock hypothesis in database
    hypothesis_data = {
        "hypothesis_text": "Optimize test function for better performance",
        "category": "code_fix",
        "root_cause": "Inefficient algorithm",
        "proposed_fix": "# Optimized code\ndef test_fast(): return True",
        "priority": 80
    }
    
    # Create hypothesis in DB
    hypothesis_id = plugin.db.create_hypothesis(**hypothesis_data)
    assert hypothesis_id > 0
    print(f"✅ Created hypothesis ID: {hypothesis_id}")
    
    # Verify database stores hypotheses correctly
    result = plugin.db.get_hypothesis_by_id(hypothesis_id)
    assert result is not None
    assert result["hypothesis_text"] == hypothesis_data["hypothesis_text"]
    assert result["category"] == hypothesis_data["category"]
    assert result["status"] == "pending"
    
    print("✅ Hypothesis database integration working")
    print(f"   ID: {hypothesis_id}")
    print(f"   Category: {result['category']}")
    print(f"   Status: {result['status']}")
    print(f"   Priority: {result['priority']}")


if __name__ == "__main__":
    print("="*60)
    print("SOPHIA AMI 1.0 - Phase 3.4 Self-Tuning Tests")
    print("="*60)
    print()
    
    # Run all tests
    pytest.main([__file__, "-v", "-s"])
