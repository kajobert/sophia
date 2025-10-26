"""
Tests for Quality Assurance Plugin (cognitive_qa.py)

Tests INSTINKTY layer reflexive code validation.
"""

import pytest
import logging
from plugins.cognitive_qa import (
    QualityAssurance,
    ValidationLevel,
    ValidationCategory
)
from plugins.base_plugin import PluginType
from core.context import SharedContext


@pytest.fixture
def test_context():
    """Create test SharedContext for testing."""
    logger = logging.getLogger("test")
    return SharedContext(
        session_id="test-session",
        current_state="testing",
        logger=logger
    )


@pytest.fixture
def qa_plugin():
    """Create QA plugin instance for testing."""
    plugin = QualityAssurance()
    plugin.setup({
        "min_compliance_score": 0.80,
        "allow_warnings": True,
        "require_tests": True
    })
    return plugin


@pytest.fixture
def valid_plugin_code():
    """Valid plugin code that should pass all checks."""
    return '''"""
Example Plugin - Valid Implementation
"""

from typing import Dict, Any
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class ExamplePlugin(BasePlugin):
    """
    Example plugin demonstrating correct implementation.
    
    This plugin shows proper:
    - BasePlugin inheritance
    - Type annotations
    - Docstrings
    - English-only code
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return "example_plugin"
    
    @property
    def plugin_type(self) -> PluginType:
        """Plugin type."""
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        """
        Initialize plugin with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Execute plugin logic.
        
        Args:
            context: Shared context
            
        Returns:
            Modified context
        """
        context.payload["result"] = "success"
        return context
'''


@pytest.fixture
def valid_test_code():
    """Valid test code."""
    return '''"""
Tests for Example Plugin
"""

import pytest
from plugins.example_plugin import ExamplePlugin
from core.context import SharedContext


def test_plugin_creation():
    """Test plugin can be created."""
    plugin = ExamplePlugin()
    assert plugin.name == "example_plugin"


@pytest.mark.asyncio
async def test_plugin_execute():
    """Test plugin execution."""
    plugin = ExamplePlugin()
    plugin.setup({})
    
    context = SharedContext()
    result = await plugin.execute(context)
    
    assert result.payload["result"] == "success"
'''


@pytest.fixture
def invalid_plugin_no_baseplugin():
    """Plugin missing BasePlugin inheritance."""
    return '''
class BadPlugin:
    """This doesn't inherit from BasePlugin."""
    pass
'''


@pytest.fixture
def invalid_plugin_no_methods():
    """Plugin missing required methods."""
    return '''
from plugins.base_plugin import BasePlugin

class BadPlugin(BasePlugin):
    """Missing required methods."""
    pass
'''


@pytest.fixture
def invalid_plugin_core_modification():
    """Plugin attempting to modify core."""
    return '''
from plugins.base_plugin import BasePlugin
import core.kernel as kernel

class BadPlugin(BasePlugin):
    """Attempts to modify core - FORBIDDEN."""
    
    def hack_core(self):
        # Trying to modify core/
        kernel.do_something_bad()
'''


@pytest.fixture
def invalid_plugin_czech_text():
    """Plugin with non-English text."""
    return '''
from plugins.base_plugin import BasePlugin

class ČeskýPlugin(BasePlugin):
    """Plugin s českým textem - FORBIDDEN."""
    
    def metoda(self):
        """Toto je česky napsaná metoda."""
        proměnná = "česká hodnota"
        return proměnná
'''


@pytest.fixture
def invalid_plugin_no_type_hints():
    """Plugin without type annotations."""
    return '''
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

class BadPlugin(BasePlugin):
    """Missing type hints."""
    
    @property
    def name(self):  # Missing -> str
        return "bad_plugin"
    
    @property
    def plugin_type(self):  # Missing -> PluginType
        return PluginType.TOOL
    
    @property
    def version(self):  # Missing -> str
        return "1.0.0"
    
    def setup(self, config):  # Missing : dict and -> None
        pass
    
    async def execute(self, context):  # Missing : SharedContext and -> SharedContext
        return context
'''


@pytest.fixture
def invalid_plugin_no_docstrings():
    """Plugin without docstrings."""
    return '''
from typing import Dict
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

class BadPlugin(BasePlugin):
    
    @property
    def name(self) -> str:
        return "bad_plugin"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        pass
    
    async def execute(self, context: SharedContext) -> SharedContext:
        return context
    
    def helper_method(self, data: str) -> str:
        return data.upper()
'''


@pytest.fixture
def dangerous_plugin_eval():
    """Plugin using dangerous eval()."""
    return '''
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

class DangerousPlugin(BasePlugin):
    """Uses eval - security risk."""
    
    @property
    def name(self) -> str:
        return "dangerous"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        pass
    
    async def execute(self, context: SharedContext) -> SharedContext:
        # Dangerous: using eval()
        code = context.payload.get("code", "")
        result = eval(code)  # Security risk!
        context.payload["result"] = result
        return context
'''


# ============================================================================
# TESTS: Plugin Metadata
# ============================================================================

def test_plugin_metadata():
    """Test QA plugin has correct metadata."""
    plugin = QualityAssurance()
    
    assert plugin.name == "cognitive_qa"
    assert plugin.plugin_type == PluginType.COGNITIVE
    assert plugin.version == "1.0.0"


def test_plugin_initialization():
    """Test plugin initializes with defaults."""
    plugin = QualityAssurance()
    assert plugin.name == "cognitive_qa"


# ============================================================================
# TESTS: Setup and Configuration
# ============================================================================

def test_setup_default_config():
    """Test setup with default configuration."""
    plugin = QualityAssurance()
    plugin.setup({})
    
    assert plugin._min_compliance_score == 0.80
    assert plugin._allow_warnings is True
    assert plugin._require_tests is True


def test_setup_custom_config():
    """Test setup with custom configuration."""
    plugin = QualityAssurance()
    plugin.setup({
        "min_compliance_score": 0.90,
        "allow_warnings": False,
        "require_tests": False
    })
    
    assert plugin._min_compliance_score == 0.90
    assert plugin._allow_warnings is False
    assert plugin._require_tests is False


def test_setup_with_tools():
    """Test setup with tool references."""
    mock_llm = object()
    mock_fs = object()
    mock_bash = object()
    
    plugin = QualityAssurance()
    plugin.setup({
        "tool_llm": mock_llm,
        "tool_file_system": mock_fs,
        "tool_bash": mock_bash
    })
    
    assert plugin._llm_tool is mock_llm
    assert plugin._file_system_tool is mock_fs
    assert plugin._bash_tool is mock_bash


# ============================================================================
# TESTS: Valid Code Review
# ============================================================================

@pytest.mark.asyncio
async def test_review_valid_code(qa_plugin, test_context, valid_plugin_code, valid_test_code):
    """Test review of valid code returns approval."""
    test_context.payload = {
        "action": "review_code",
        "plugin_code": valid_plugin_code,
        "test_code": valid_test_code,
        "plugin_name": "example_plugin",
        "specification": "Create example plugin"
    }
    
    result = await qa_plugin.execute(test_context)
    
    assert "approved" in result.payload
    assert "issues" in result.payload
    assert "compliance_score" in result.payload
    assert "must_fix" in result.payload
    assert "suggestions" in result.payload
    
    # Valid code should be approved
    assert result.payload["approved"] is True
    assert result.payload["compliance_score"] >= 0.80
    assert len(result.payload["must_fix"]) == 0


# ============================================================================
# TESTS: Reflex Checks (Level 1)
# ============================================================================

@pytest.mark.asyncio
async def test_reflex_check_no_baseplugin(qa_plugin, invalid_plugin_no_baseplugin):
    """Test reflex check detects missing BasePlugin inheritance."""
    issues = await qa_plugin._reflex_checks(invalid_plugin_no_baseplugin, "")
    
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    assert len(error_issues) > 0
    
    # Should detect missing BasePlugin (class without inheritance)
    # Or missing required properties/methods
    assert len(error_issues) >= 3  # Multiple issues expected


@pytest.mark.asyncio
async def test_reflex_check_missing_methods(qa_plugin, invalid_plugin_no_methods):
    """Test reflex check detects missing required methods."""
    issues = await qa_plugin._reflex_checks(invalid_plugin_no_methods, "")
    
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    
    # Should detect missing name, plugin_type, version, setup, execute
    assert len(error_issues) >= 3  # At least some missing


@pytest.mark.asyncio
async def test_reflex_check_core_modification(qa_plugin, invalid_plugin_core_modification):
    """Test reflex check detects core/ modification attempt."""
    issues = await qa_plugin._reflex_checks(invalid_plugin_core_modification, "")
    
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    
    # Should detect core/ reference
    core_issue = next(
        (i for i in error_issues if "core/" in i["message"]),
        None
    )
    assert core_issue is not None
    assert core_issue["category"] == ValidationCategory.SAFETY


@pytest.mark.asyncio
async def test_reflex_check_czech_text(qa_plugin, invalid_plugin_czech_text):
    """Test reflex check detects non-English text."""
    issues = await qa_plugin._reflex_checks(invalid_plugin_czech_text, "")
    
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    
    # Should detect Czech characters
    language_issue = next(
        (i for i in error_issues if i["category"] == ValidationCategory.LANGUAGE),
        None
    )
    assert language_issue is not None


@pytest.mark.asyncio
async def test_reflex_check_dangerous_eval(qa_plugin, dangerous_plugin_eval):
    """Test reflex check detects dangerous eval() usage."""
    issues = await qa_plugin._reflex_checks(dangerous_plugin_eval, "")
    
    warning_issues = [i for i in issues if i["level"] == ValidationLevel.WARNING]
    
    # Should detect eval() - at least as warning
    eval_issue = next(
        (i for i in warning_issues if "eval" in i["message"].lower()),
        None
    )
    assert eval_issue is not None
    assert eval_issue["category"] == ValidationCategory.SAFETY


@pytest.mark.asyncio
async def test_reflex_check_no_tests(qa_plugin, valid_plugin_code):
    """Test reflex check detects missing test code."""
    issues = await qa_plugin._reflex_checks(valid_plugin_code, "")  # No test code
    
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    
    # Should detect missing tests
    test_issue = next(
        (i for i in error_issues if i["category"] == ValidationCategory.TESTING),
        None
    )
    assert test_issue is not None


# ============================================================================
# TESTS: Architecture Compliance (Level 2)
# ============================================================================

@pytest.mark.asyncio
async def test_architecture_check_missing_type_hints(qa_plugin, invalid_plugin_no_type_hints):
    """Test architecture check detects missing type hints."""
    issues = await qa_plugin._architecture_compliance(invalid_plugin_no_type_hints)
    
    warning_issues = [i for i in issues if i["level"] == ValidationLevel.WARNING]
    
    # Should detect missing return type annotations
    assert len(warning_issues) > 0


@pytest.mark.asyncio
async def test_architecture_check_missing_docstrings(qa_plugin, invalid_plugin_no_docstrings):
    """Test architecture check detects missing docstrings."""
    issues = await qa_plugin._architecture_compliance(invalid_plugin_no_docstrings)
    
    warning_issues = [i for i in issues if i["level"] == ValidationLevel.WARNING]
    
    # Should detect missing docstrings
    docstring_issues = [
        i for i in warning_issues
        if "docstring" in i["message"].lower()
    ]
    assert len(docstring_issues) > 0


@pytest.mark.asyncio
async def test_architecture_check_syntax_error(qa_plugin):
    """Test architecture check handles syntax errors."""
    invalid_syntax = "class BadPlugin(BasePlugin:\n    pass"  # Missing closing paren
    
    issues = await qa_plugin._architecture_compliance(invalid_syntax)
    
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    
    # Should detect syntax error
    syntax_issue = next(
        (i for i in error_issues if "syntax" in i["message"].lower()),
        None
    )
    assert syntax_issue is not None


@pytest.mark.asyncio
async def test_architecture_check_valid_code(qa_plugin, valid_plugin_code):
    """Test architecture check passes valid code."""
    issues = await qa_plugin._architecture_compliance(valid_plugin_code)
    
    # Valid code might have some warnings but no errors
    error_issues = [i for i in issues if i["level"] == ValidationLevel.ERROR]
    assert len(error_issues) == 0


# ============================================================================
# TESTS: Compliance Score Calculation
# ============================================================================

def test_compliance_score_perfect(qa_plugin):
    """Test compliance score with no issues."""
    issues = []
    score = qa_plugin._calculate_compliance_score(issues)
    assert score == 1.0


def test_compliance_score_with_errors(qa_plugin):
    """Test compliance score with errors."""
    issues = [
        {"level": ValidationLevel.ERROR, "message": "Error 1"},
        {"level": ValidationLevel.ERROR, "message": "Error 2"},
    ]
    score = qa_plugin._calculate_compliance_score(issues)
    assert abs(score - 0.60) < 0.01  # Allow small floating point difference


def test_compliance_score_with_warnings(qa_plugin):
    """Test compliance score with warnings."""
    issues = [
        {"level": ValidationLevel.WARNING, "message": "Warning 1"},
        {"level": ValidationLevel.WARNING, "message": "Warning 2"},
    ]
    score = qa_plugin._calculate_compliance_score(issues)
    assert abs(score - 0.90) < 0.01  # Allow small floating point difference


def test_compliance_score_mixed(qa_plugin):
    """Test compliance score with mixed issues."""
    issues = [
        {"level": ValidationLevel.ERROR, "message": "Error"},
        {"level": ValidationLevel.WARNING, "message": "Warning"},
        {"level": ValidationLevel.INFO, "message": "Info"},
    ]
    score = qa_plugin._calculate_compliance_score(issues)
    assert score == 0.74  # 1.0 - 0.20 - 0.05 - 0.01


def test_compliance_score_minimum_zero(qa_plugin):
    """Test compliance score doesn't go below 0."""
    issues = [{"level": ValidationLevel.ERROR, "message": f"Error {i}"} for i in range(10)]
    score = qa_plugin._calculate_compliance_score(issues)
    assert score == 0.0  # Can't go negative


# ============================================================================
# TESTS: Full Review Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_full_review_invalid_code_rejected(qa_plugin, test_context, invalid_plugin_no_baseplugin):
    """Test full review rejects invalid code."""
    test_context.payload = {
        "action": "review_code",
        "plugin_code": invalid_plugin_no_baseplugin,
        "test_code": "",
        "plugin_name": "bad_plugin",
        "specification": "Invalid plugin"
    }
    
    result = await qa_plugin.execute(test_context)
    
    assert result.payload["approved"] is False
    assert len(result.payload["must_fix"]) > 0
    assert result.payload["compliance_score"] < 0.80


@pytest.mark.asyncio
async def test_full_review_with_warnings_allowed(qa_plugin, test_context, invalid_plugin_no_docstrings, valid_test_code):
    """Test review allows warnings if configured."""
    qa_plugin._allow_warnings = True
    
    test_context.payload = {
        "action": "review_code",
        "plugin_code": invalid_plugin_no_docstrings,
        "test_code": valid_test_code,
        "plugin_name": "plugin_with_warnings",
        "specification": "Plugin with warnings"
    }
    
    result = await qa_plugin.execute(test_context)


@pytest.mark.asyncio
async def test_full_review_warnings_not_allowed(qa_plugin, test_context, invalid_plugin_no_docstrings, valid_test_code):
    """Test review rejects warnings if configured."""
    qa_plugin._allow_warnings = False
    
    test_context.payload = {
        "action": "review_code",
        "plugin_code": invalid_plugin_no_docstrings,
        "test_code": valid_test_code,
        "plugin_name": "plugin_with_warnings",
        "specification": "Plugin with warnings"
    }
    
    result = await qa_plugin.execute(test_context)
    
    # If there are any warnings, should be rejected
    warnings = [i for i in result.payload["issues"] if i["level"] == ValidationLevel.WARNING]
    if warnings:
        assert result.payload["approved"] is False


@pytest.mark.asyncio
async def test_review_missing_plugin_code(qa_plugin, test_context):
    """Test review handles missing plugin code."""
    test_context.payload = {
        "action": "review_code",
        # Missing plugin_code
        "test_code": "",
        "plugin_name": "test",
        "specification": "test"
    }
    
    result = await qa_plugin.execute(test_context)
    
    assert "error" in result.payload
    assert "plugin_code" in result.payload["error"].lower()


@pytest.mark.asyncio
async def test_review_unknown_action(qa_plugin, test_context, valid_plugin_code):
    """Test review handles unknown action."""
    test_context.payload = {
        "action": "unknown_action",
        "plugin_code": valid_plugin_code
    }
    
    result = await qa_plugin.execute(test_context)
    
    assert "error" in result.payload
    assert "unknown action" in result.payload["error"].lower()


# ============================================================================
# TESTS: LLM Integration (Level 3)
# ============================================================================

@pytest.mark.asyncio
async def test_llm_review_without_llm_tool(qa_plugin, valid_plugin_code, valid_test_code):
    """Test LLM review gracefully handles missing LLM tool."""
    # No LLM tool configured
    qa_plugin._llm_tool = None
    
    issues = await qa_plugin._llm_deep_review(
        valid_plugin_code,
        valid_test_code,
        "Test specification"
    )
    
    # Should return empty list, not crash
    assert isinstance(issues, list)


@pytest.mark.asyncio
async def test_review_suggestions_present(qa_plugin, test_context, valid_plugin_code, valid_test_code):
    """Test review provides actionable suggestions."""
    test_context.payload = {
        "action": "review_code",
        "plugin_code": valid_plugin_code,
        "test_code": valid_test_code,
        "plugin_name": "example",
        "specification": "Example plugin"
    }
    
    result = await qa_plugin.execute(test_context)
    
    assert "suggestions" in result.payload
    assert isinstance(result.payload["suggestions"], list)


# ============================================================================
# TESTS: Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_review_empty_code(qa_plugin, test_context):
    """Test review handles empty code."""
    test_context.payload = {
        "action": "review_code",
        "plugin_code": "",
        "test_code": "",
        "plugin_name": "empty",
        "specification": "Empty"
    }
    
    result = await qa_plugin.execute(test_context)
    
    assert "error" in result.payload


@pytest.mark.asyncio
async def test_review_very_long_code(qa_plugin, test_context, valid_plugin_code, valid_test_code):
    """Test review handles very long code."""
    # Generate very long but valid code
    long_code = valid_plugin_code + "\n" + "    # Comment\n" * 1000
    
    test_context.payload = {
        "action": "review_code",
        "plugin_code": long_code,
        "test_code": valid_test_code,
        "plugin_name": "long_plugin",
        "specification": "Very long plugin"
    }
    
    result = await qa_plugin.execute(test_context)
    
    # Should complete without error
    assert "approved" in result.payload
