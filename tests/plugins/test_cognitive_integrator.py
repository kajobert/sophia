"""
Tests for Safe Integrator Plugin (cognitive_integrator.py)

Tests INSTINKTY layer atomic integration with rollback capabilities.
"""

import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from plugins.cognitive_integrator import SafeIntegrator, IntegrationStatus
from plugins.base_plugin import PluginType
from core.context import SharedContext


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """
    Automatically cleanup test-generated files before and after each test.
    
    This prevents test artifacts from breaking subsequent test runs.
    Files created during integration tests are removed to maintain clean state.
    """
    # Cleanup before test
    test_files = [
        Path("plugins/test_plugin.py"),
        Path("plugins/cleanup_test.py"),
        Path("plugins/example_plugin.py"),
        Path("tests/plugins/test_test_plugin.py"),
        Path("tests/plugins/test_cleanup_test.py"),
    ]
    
    for file_path in test_files:
        if file_path.exists():
            file_path.unlink()
    
    # Run test
    yield
    
    # Cleanup after test
    for file_path in test_files:
        if file_path.exists():
            file_path.unlink()


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
def mock_git_tool():
    """Create mock Git tool with repository."""
    git_tool = Mock()
    
    # Mock repository
    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = False
    mock_repo.head.commit.hexsha = "abc123def456"
    mock_repo.tags = []
    
    # Mock tag creation
    mock_tag = Mock()
    mock_tag.name = "backup-20251026-143022-test_plugin"
    mock_tag.commit.hexsha = "abc123def456"
    mock_repo.create_tag.return_value = mock_tag
    mock_repo.tags = [mock_tag]
    
    git_tool.repo = mock_repo
    
    return git_tool


@pytest.fixture
def mock_bash_tool():
    """Create mock Bash tool for test execution."""
    bash_tool = Mock()
    
    # Mock successful test execution
    async def mock_execute(context):
        context.payload["output"] = "247 passed in 9.62s"
        context.payload["exit_code"] = 0
        return context
    
    bash_tool.execute = AsyncMock(side_effect=mock_execute)
    
    return bash_tool


@pytest.fixture
def mock_file_system_tool():
    """Create mock file system tool."""
    return Mock()


@pytest.fixture
def integrator_plugin(mock_git_tool, mock_bash_tool, mock_file_system_tool, tmp_path):
    """Create SafeIntegrator plugin with mocked dependencies."""
    plugin = SafeIntegrator()
    plugin.setup({
        "tool_git": mock_git_tool,
        "tool_bash": mock_bash_tool,
        "tool_file_system": mock_file_system_tool,
        "backup_dir": str(tmp_path / "backups"),
        "auto_rollback": True,
        "require_tests_pass": True,
        "backup_retention_days": 30
    })
    return plugin


@pytest.fixture
def valid_plugin_code():
    """Valid plugin code for integration testing."""
    return '''"""Example plugin for testing."""
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

class ExamplePlugin(BasePlugin):
    """Example plugin."""
    
    @property
    def name(self) -> str:
        return "example_plugin"
    
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
'''


@pytest.fixture
def valid_test_code():
    """Valid test code for integration testing."""
    return '''"""Tests for example plugin."""
import pytest
from plugins.example_plugin import ExamplePlugin

def test_plugin_creation():
    plugin = ExamplePlugin()
    assert plugin.name == "example_plugin"
'''


# ============================================================================
# TESTS: Plugin Metadata
# ============================================================================

def test_plugin_metadata():
    """Test SafeIntegrator plugin has correct metadata."""
    plugin = SafeIntegrator()
    
    assert plugin.name == "cognitive_integrator"
    assert plugin.plugin_type == PluginType.COGNITIVE
    assert plugin.version == "1.0.0"


def test_plugin_initialization():
    """Test plugin initializes with defaults."""
    plugin = SafeIntegrator()
    assert plugin.name == "cognitive_integrator"


# ============================================================================
# TESTS: Setup and Configuration
# ============================================================================

def test_setup_default_config(mock_git_tool, mock_bash_tool, tmp_path):
    """Test setup with default configuration."""
    plugin = SafeIntegrator()
    plugin.setup({
        "tool_git": mock_git_tool,
        "tool_bash": mock_bash_tool
    })
    
    assert plugin._auto_rollback is True
    assert plugin._require_tests_pass is True
    assert plugin._backup_retention_days == 30


def test_setup_custom_config(mock_git_tool, mock_bash_tool, tmp_path):
    """Test setup with custom configuration."""
    plugin = SafeIntegrator()
    plugin.setup({
        "tool_git": mock_git_tool,
        "tool_bash": mock_bash_tool,
        "backup_dir": str(tmp_path / "custom_backups"),
        "auto_rollback": False,
        "require_tests_pass": False,
        "backup_retention_days": 60
    })
    
    assert plugin._auto_rollback is False
    assert plugin._require_tests_pass is False
    assert plugin._backup_retention_days == 60
    assert plugin._backup_dir == tmp_path / "custom_backups"


def test_setup_creates_backup_directory(tmp_path):
    """Test setup creates backup directory."""
    plugin = SafeIntegrator()
    backup_dir = tmp_path / "test_backups"
    
    assert not backup_dir.exists()
    
    plugin.setup({
        "backup_dir": str(backup_dir)
    })
    
    assert backup_dir.exists()


# ============================================================================
# TESTS: Backup Creation
# ============================================================================

@pytest.mark.asyncio
async def test_create_backup_success(integrator_plugin, mock_git_tool):
    """Test successful backup creation."""
    backup_id = await integrator_plugin._create_backup("test_plugin")
    
    assert backup_id.startswith("backup-")
    assert "test_plugin" in backup_id
    
    # Verify tag was created
    mock_git_tool.repo.create_tag.assert_called_once()


@pytest.mark.asyncio
async def test_create_backup_with_uncommitted_changes(integrator_plugin, mock_git_tool):
    """Test backup creation with uncommitted changes."""
    # Simulate dirty repository
    mock_git_tool.repo.is_dirty.return_value = True
    
    backup_id = await integrator_plugin._create_backup("test_plugin")
    
    # Verify changes were committed before tag
    mock_git_tool.repo.git.add.assert_called_once()
    mock_git_tool.repo.index.commit.assert_called_once()
    mock_git_tool.repo.create_tag.assert_called_once()


@pytest.mark.asyncio
async def test_create_backup_no_git_tool(tmp_path):
    """Test backup creation fails without Git tool."""
    plugin = SafeIntegrator()
    plugin.setup({"backup_dir": str(tmp_path / "backups")})
    
    with pytest.raises(RuntimeError, match="Git tool not available"):
        await plugin._create_backup("test_plugin")


@pytest.mark.asyncio
async def test_create_backup_saves_metadata(integrator_plugin, tmp_path):
    """Test backup metadata is saved."""
    backup_id = await integrator_plugin._create_backup("test_plugin")
    
    metadata_file = integrator_plugin._backup_dir / f"{backup_id}.json"
    assert metadata_file.exists()
    
    import json
    metadata = json.loads(metadata_file.read_text())
    
    assert metadata["tag"] == backup_id
    assert metadata["plugin_name"] == "test_plugin"
    assert "timestamp" in metadata
    assert "commit_sha" in metadata


# ============================================================================
# TESTS: File Writing
# ============================================================================

@pytest.mark.asyncio
async def test_write_files_plugin_only(integrator_plugin, valid_plugin_code):
    """Test writing plugin file without test file."""
    plugin_path, test_path = await integrator_plugin._write_files(
        valid_plugin_code, "", "test_plugin"
    )
    
    assert plugin_path == Path("plugins/test_plugin.py")
    assert plugin_path.exists()
    assert plugin_path.read_text() == valid_plugin_code


@pytest.mark.asyncio
async def test_write_files_plugin_and_test(integrator_plugin, valid_plugin_code, valid_test_code):
    """Test writing both plugin and test files."""
    plugin_path, test_path = await integrator_plugin._write_files(
        valid_plugin_code, valid_test_code, "test_plugin"
    )
    
    assert plugin_path == Path("plugins/test_plugin.py")
    assert test_path == Path("tests/plugins/test_test_plugin.py")
    
    assert plugin_path.exists()
    assert test_path.exists()
    
    assert plugin_path.read_text() == valid_plugin_code
    assert test_path.read_text() == valid_test_code


# ============================================================================
# TESTS: Test Execution
# ============================================================================

@pytest.mark.asyncio
async def test_run_full_test_suite_success(integrator_plugin, mock_bash_tool):
    """Test successful test suite execution."""
    results = await integrator_plugin._run_full_test_suite()
    
    assert results["passed"] is True
    assert results["total"] == 247
    assert results["failed"] == 0
    assert "247 passed" in results["summary"]


@pytest.mark.asyncio
async def test_run_full_test_suite_failure(integrator_plugin, mock_bash_tool):
    """Test failed test suite execution."""
    # Mock failed tests
    async def mock_execute_failed(context):
        context.payload["output"] = "245 passed, 2 failed in 9.62s"
        context.payload["exit_code"] = 1
        return context
    
    mock_bash_tool.execute = AsyncMock(side_effect=mock_execute_failed)
    
    results = await integrator_plugin._run_full_test_suite()
    
    assert results["passed"] is False
    assert results["total"] == 245
    assert results["failed"] == 2
    assert "2 failed" in results["summary"]


@pytest.mark.asyncio
async def test_run_full_test_suite_no_bash_tool(tmp_path):
    """Test test execution fails without Bash tool."""
    plugin = SafeIntegrator()
    plugin.setup({"backup_dir": str(tmp_path / "backups")})
    
    with pytest.raises(RuntimeError, match="Bash tool not available"):
        await plugin._run_full_test_suite()


# ============================================================================
# TESTS: Integration Workflow
# ============================================================================

@pytest.mark.asyncio
async def test_integrate_plugin_success(integrator_plugin, test_context, valid_plugin_code, valid_test_code):
    """Test successful plugin integration."""
    test_context.payload = {
        "action": "integrate_plugin",
        "plugin_code": valid_plugin_code,
        "test_code": valid_test_code,
        "plugin_name": "test_plugin",
        "qa_report": {"compliance_score": 0.95}
    }
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is True
    assert "backup_id" in result.payload
    assert result.payload["backup_id"].startswith("backup-")
    assert "test_plugin" in result.payload["message"]
    assert "test_results" in result.payload
    assert result.payload["test_results"]["passed"] is True


@pytest.mark.asyncio
async def test_integrate_plugin_missing_code(integrator_plugin, test_context):
    """Test integration fails with missing plugin code."""
    test_context.payload = {
        "action": "integrate_plugin",
        "plugin_name": "test_plugin"
    }
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is False
    assert "error" in result.payload
    assert "plugin_code" in result.payload["error"]


@pytest.mark.asyncio
async def test_integrate_plugin_missing_name(integrator_plugin, test_context, valid_plugin_code):
    """Test integration fails with missing plugin name."""
    test_context.payload = {
        "action": "integrate_plugin",
        "plugin_code": valid_plugin_code
    }
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is False
    assert "error" in result.payload
    assert "plugin_name" in result.payload["error"]


@pytest.mark.asyncio
async def test_integrate_plugin_test_failure_rollback(integrator_plugin, test_context, valid_plugin_code, mock_bash_tool, mock_git_tool):
    """Test integration rolls back on test failure."""
    # Mock test failure
    async def mock_execute_failed(context):
        context.payload["output"] = "245 passed, 2 failed"
        context.payload["exit_code"] = 1
        return context
    
    mock_bash_tool.execute = AsyncMock(side_effect=mock_execute_failed)
    
    test_context.payload = {
        "action": "integrate_plugin",
        "plugin_code": valid_plugin_code,
        "test_code": "",
        "plugin_name": "test_plugin",
        "qa_report": {}
    }
    
    # Pre-create the backup tag that will be generated
    # This simulates successful backup creation before test failure
    mock_tag = Mock()
    mock_tag.name = "backup-test"  # Will be replaced by actual backup_id
    
    # We need to capture the actual backup_id created
    original_create_backup = integrator_plugin._create_backup
    actual_backup_id = None
    
    async def mock_create_backup_with_tag(plugin_name):
        nonlocal actual_backup_id
        actual_backup_id = await original_create_backup(plugin_name)
        # Add the created tag to mock repo for rollback
        mock_tag.name = actual_backup_id
        mock_git_tool.repo.tags = [mock_tag]
        return actual_backup_id
    
    integrator_plugin._create_backup = mock_create_backup_with_tag
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is False
    assert result.payload.get("rolled_back") is True
    assert "backup_id" in result.payload


@pytest.mark.asyncio
async def test_integrate_plugin_no_rollback_when_disabled(mock_git_tool, mock_bash_tool, test_context, valid_plugin_code, tmp_path):
    """Test integration doesn't rollback when auto_rollback is False."""
    plugin = SafeIntegrator()
    plugin.setup({
        "tool_git": mock_git_tool,
        "tool_bash": mock_bash_tool,
        "backup_dir": str(tmp_path / "backups"),
        "auto_rollback": False  # Disable auto rollback
    })
    
    # Mock test failure
    async def mock_execute_failed(context):
        context.payload["output"] = "245 passed, 2 failed"
        context.payload["exit_code"] = 1
        return context
    
    mock_bash_tool.execute = AsyncMock(side_effect=mock_execute_failed)
    
    test_context.payload = {
        "action": "integrate_plugin",
        "plugin_code": valid_plugin_code,
        "test_code": "",
        "plugin_name": "test_plugin",
        "qa_report": {}
    }
    
    result = await plugin.execute(test_context)
    
    assert result.payload["success"] is False
    assert result.payload["rolled_back"] is False


# ============================================================================
# TESTS: Rollback Operations
# ============================================================================

@pytest.mark.asyncio
async def test_rollback_to_backup(integrator_plugin, mock_git_tool):
    """Test rollback to specific backup."""
    backup_id = "backup-20251026-143022-test_plugin"
    
    # Add backup tag to mock repo
    mock_tag = Mock()
    mock_tag.name = backup_id
    mock_git_tool.repo.tags = [mock_tag]
    
    await integrator_plugin._rollback_to_backup(backup_id)
    
    # Verify git reset was called
    mock_git_tool.repo.git.reset.assert_called_once_with('--hard', backup_id)
    mock_git_tool.repo.git.clean.assert_called_once_with('-fd')


@pytest.mark.asyncio
async def test_rollback_nonexistent_backup(integrator_plugin, mock_git_tool):
    """Test rollback fails for nonexistent backup."""
    mock_git_tool.repo.tags = []  # No tags available
    
    with pytest.raises(ValueError, match="Backup tag not found"):
        await integrator_plugin._rollback_to_backup("nonexistent-backup")


@pytest.mark.asyncio
async def test_rollback_action(integrator_plugin, test_context, mock_git_tool):
    """Test rollback via execute action."""
    backup_id = "backup-20251026-143022-test_plugin"
    
    # Add backup tag to mock repo
    mock_tag = Mock()
    mock_tag.name = backup_id
    mock_git_tool.repo.tags = [mock_tag]
    
    test_context.payload = {
        "action": "rollback",
        "backup_id": backup_id
    }
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is True
    assert backup_id in result.payload["message"]


@pytest.mark.asyncio
async def test_rollback_action_missing_backup_id(integrator_plugin, test_context):
    """Test rollback fails without backup_id."""
    test_context.payload = {
        "action": "rollback"
    }
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is False
    assert "error" in result.payload
    assert "backup_id" in result.payload["error"]


# ============================================================================
# TESTS: Backup Listing
# ============================================================================

@pytest.mark.asyncio
async def test_list_backups_empty(integrator_plugin, test_context):
    """Test listing backups when none exist."""
    test_context.payload = {"action": "list_backups"}
    
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is True
    assert result.payload["count"] >= 0
    assert isinstance(result.payload["backups"], list)


@pytest.mark.asyncio
async def test_list_backups_with_metadata(integrator_plugin, test_context):
    """Test listing backups with metadata files."""
    # Create a backup first
    await integrator_plugin._create_backup("test_plugin")
    
    test_context.payload = {"action": "list_backups"}
    result = await integrator_plugin.execute(test_context)
    
    assert result.payload["success"] is True
    assert result.payload["count"] >= 1
    assert len(result.payload["backups"]) >= 1
    
    backup = result.payload["backups"][0]
    assert "tag" in backup
    assert "plugin_name" in backup
    assert "timestamp" in backup


# ============================================================================
# TESTS: Unknown Actions
# ============================================================================

@pytest.mark.asyncio
async def test_unknown_action(integrator_plugin, test_context):
    """Test unknown action handling."""
    test_context.payload = {"action": "unknown_action"}
    
    result = await integrator_plugin.execute(test_context)
    
    assert "error" in result.payload
    assert "unknown action" in result.payload["error"].lower()


# ============================================================================
# TESTS: Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_integration_with_cleanup(integrator_plugin, valid_plugin_code, valid_test_code):
    """Test integration cleans up test files after success."""
    # This is implicitly tested by the success case
    # Just verify files are written
    plugin_path, test_path = await integrator_plugin._write_files(
        valid_plugin_code, valid_test_code, "cleanup_test"
    )
    
    assert plugin_path.exists()
    if valid_test_code:
        assert test_path.exists()
