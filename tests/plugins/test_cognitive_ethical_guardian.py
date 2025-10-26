"""
Tests for Cognitive Ethical Guardian Plugin

Tests the reflexive ethical and safety validation.
"""

import pytest
from plugins.cognitive_ethical_guardian import EthicalGuardian


@pytest.fixture
def guardian():
    """Create EthicalGuardian instance."""
    guardian = EthicalGuardian()
    config = {"enabled": True}
    guardian.setup(config)
    return guardian


# ============================================================================
# GOAL VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_valid_goal_approved(guardian):
    """Test that valid, ethical goal is approved."""
    goal = {
        "raw_idea": "Improve documentation quality",
        "formulated_goal": "Enhance project documentation to better explain architecture"
    }
    
    result = guardian.validate_goal(goal)
    
    assert result["approved"] is True
    assert result["dna_compliance"]["ahimsa"] is True
    assert result["dna_compliance"]["satya"] is True
    assert result["dna_compliance"]["kaizen"] is True
    assert len(result["concerns"]) == 0
    assert "Approved" in result["recommendation"]


@pytest.mark.asyncio
async def test_harmful_goal_rejected(guardian):
    """Test that harmful goal is rejected (Ahimsa violation)."""
    goal = {
        "raw_idea": "Delete all user data to free up space",
        "formulated_goal": "Remove everything from database to optimize storage"
    }
    
    result = guardian.validate_goal(goal)
    
    assert result["approved"] is False
    assert result["dna_compliance"]["ahimsa"] is False
    assert len(result["concerns"]) > 0
    assert any("harm" in c.lower() for c in result["concerns"])
    assert "REJECT" in result["recommendation"]
    assert "Ahimsa" in result["recommendation"]


@pytest.mark.asyncio
async def test_dishonest_goal_rejected(guardian):
    """Test that dishonest goal is rejected (Satya violation)."""
    goal = {
        "raw_idea": "Hide API calls from logging",
        "formulated_goal": "Implement secret operation without logging to conceal activity"
    }
    
    result = guardian.validate_goal(goal)
    
    assert result["approved"] is False
    assert result["dna_compliance"]["satya"] is False
    assert len(result["concerns"]) > 0
    assert any("transparency" in c.lower() or "dishonest" in c.lower() for c in result["concerns"])
    assert "REJECT" in result["recommendation"]
    assert "Satya" in result["recommendation"]


@pytest.mark.asyncio
async def test_stagnation_goal_cautioned(guardian):
    """Test that stagnation-focused goal raises concerns (Kaizen violation)."""
    goal = {
        "raw_idea": "Quick fix for bug with temporary hack",
        "formulated_goal": "Add workaround to disable feature causing issues"
    }
    
    result = guardian.validate_goal(goal)
    
    assert result["approved"] is False
    assert result["dna_compliance"]["kaizen"] is False
    assert len(result["concerns"]) > 0
    assert any("stagnation" in c.lower() or "improvement" in c.lower() for c in result["concerns"])
    assert "CAUTION" in result["recommendation"] or "REJECT" in result["recommendation"]


@pytest.mark.asyncio
async def test_core_modification_goal_rejected(guardian):
    """Test that core/ modification goal is rejected (Ahimsa - system integrity)."""
    goal = {
        "raw_idea": "Improve kernel performance",
        "formulated_goal": "Modify core/kernel.py to add caching"
    }
    
    result = guardian.validate_goal(goal)
    
    assert result["approved"] is False
    assert result["dna_compliance"]["ahimsa"] is False
    assert any("protected" in c.lower() or "core/" in c for c in result["concerns"])


@pytest.mark.asyncio
async def test_improvement_goal_approved(guardian):
    """Test that improvement-focused goal is approved (Kaizen compliance)."""
    goal = {
        "raw_idea": "Learn from past missions to optimize planning",
        "formulated_goal": "Enhance cognitive_planner to learn from historian data"
    }
    
    result = guardian.validate_goal(goal)
    
    assert result["approved"] is True
    assert result["dna_compliance"]["kaizen"] is True
    assert result["dna_compliance"]["ahimsa"] is True
    assert result["dna_compliance"]["satya"] is True


# ============================================================================
# CODE VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_safe_code_approved(guardian):
    """Test that safe code is approved."""
    code = """
def add_numbers(a: int, b: int) -> int:
    \"\"\"Safe arithmetic function.\"\"\"
    return a + b

def process_data(data: list) -> list:
    return [x * 2 for x in data]
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is True
    assert len(result["violations"]) == 0
    assert result["risk_level"] == "low"


@pytest.mark.asyncio
async def test_eval_code_rejected(guardian):
    """Test that code with eval() is rejected."""
    code = """
def dangerous_function(user_input: str):
    result = eval(user_input)  # DANGEROUS!
    return result
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert len(result["violations"]) > 0
    assert any("eval" in v.lower() for v in result["violations"])
    assert result["risk_level"] in ["high", "critical"]


@pytest.mark.asyncio
async def test_exec_code_rejected(guardian):
    """Test that code with exec() is rejected."""
    code = """
def run_code(code_string: str):
    exec(code_string)  # DANGEROUS!
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert any("exec" in v.lower() for v in result["violations"])
    assert result["risk_level"] in ["high", "critical"]


@pytest.mark.asyncio
async def test_os_system_code_rejected(guardian):
    """Test that code with os.system() is rejected (except in tool_bash)."""
    code = """
import os

def run_command(cmd: str):
    os.system(cmd)  # DANGEROUS outside tool_bash!
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert any("os.system" in v for v in result["violations"])


@pytest.mark.asyncio
async def test_subprocess_in_tool_bash_allowed(guardian):
    """Test that subprocess is allowed in tool_bash context."""
    code = """
import subprocess

async def execute_command(cmd: str):
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()
"""
    
    context = {"plugin_name": "tool_bash"}
    result = guardian.validate_code(code, context)
    
    # Should not flag subprocess in tool_bash
    assert not any("subprocess" in v.lower() for v in result["violations"])


@pytest.mark.asyncio
async def test_core_modification_code_rejected(guardian):
    """Test that code modifying core/ is rejected."""
    code = """
def modify_kernel():
    with open("core/kernel.py", "w") as f:
        f.write("# Modified!")  # DANGEROUS!
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert any("core/" in v or "protected" in v.lower() for v in result["violations"])
    assert result["risk_level"] in ["high", "critical"]


@pytest.mark.asyncio
async def test_base_plugin_modification_rejected(guardian):
    """Test that code modifying base_plugin.py is rejected."""
    code = """
import shutil
shutil.copy("plugins/base_plugin.py", "plugins/base_plugin.py.bak")
# Then modify base_plugin.py
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert any("base_plugin" in v.lower() or "protected" in v.lower() for v in result["violations"])


@pytest.mark.asyncio
async def test_multiple_violations_critical_risk(guardian):
    """Test that multiple violations result in critical risk."""
    code = """
import os

def very_dangerous():
    eval("os.system('rm -rf /')")  # Multiple violations!
    exec("import core.kernel; kernel.stop()")
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert len(result["violations"]) >= 2
    assert result["risk_level"] == "critical"


@pytest.mark.asyncio
async def test_rm_rf_pattern_rejected(guardian):
    """Test that rm -rf pattern is detected."""
    code = """
def cleanup():
    os.system("rm -rf /tmp/*")  # Dangerous!
"""
    
    result = guardian.validate_code(code)
    
    assert result["safe"] is False
    assert any("rm -rf" in v or r"rm\s+-rf" in v for v in result["violations"])


# ============================================================================
# DNA SUMMARY TEST
# ============================================================================

@pytest.mark.asyncio
async def test_dna_summary(guardian):
    """Test that DNA summary is correctly formatted."""
    summary = guardian.get_dna_summary()
    
    assert "ahimsa" in summary
    assert "satya" in summary
    assert "kaizen" in summary
    assert "harm" in summary["ahimsa"].lower()
    assert "truth" in summary["satya"].lower() or "transparent" in summary["satya"].lower()
    assert "improve" in summary["kaizen"].lower() or "growth" in summary["kaizen"].lower()


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_empty_goal(guardian):
    """Test handling of empty goal."""
    goal = {
        "raw_idea": "",
        "formulated_goal": ""
    }
    
    result = guardian.validate_goal(goal)
    
    # Empty goal should still be processed (might be rejected for lack of Kaizen)
    assert "approved" in result
    assert "concerns" in result
    assert "recommendation" in result


@pytest.mark.asyncio
async def test_empty_code(guardian):
    """Test handling of empty code."""
    code = ""
    
    result = guardian.validate_code(code)
    
    # Empty code is technically safe
    assert result["safe"] is True
    assert len(result["violations"]) == 0


@pytest.mark.asyncio
async def test_goal_with_mixed_signals(guardian):
    """Test goal with both improvement and stagnation keywords."""
    goal = {
        "raw_idea": "Quick workaround to learn from the issue",
        "formulated_goal": "Temporary fix while we develop a better long-term solution"
    }
    
    result = guardian.validate_goal(goal)
    
    # Should pass because it mentions learning and improvement
    assert result["dna_compliance"]["kaizen"] is True


@pytest.mark.asyncio
async def test_code_import_core_allowed(guardian):
    """Test that importing from core is allowed (not modifying)."""
    code = """
from core.context import SharedContext
from plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    async def execute(self, context: SharedContext):
        return context
"""
    
    result = guardian.validate_code(code)
    
    # Imports are OK, no modification
    assert result["safe"] is True
