"""
Tests for Autonomous Interface Plugin

Verifies that autonomous commands are properly detected and delegated
to the Strategic Orchestrator without Core modifications.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

from plugins.interface_autonomous import AutonomousInterface
from plugins.base_plugin import PluginType
from core.context import SharedContext


@pytest.fixture
def mock_orchestrator():
    """Mock Strategic Orchestrator plugin."""
    orchestrator = MagicMock()
    orchestrator.name = "cognitive_orchestrator"
    orchestrator.plugin_type = PluginType.COGNITIVE
    
    # Mock execute to return successful analysis
    async def mock_execute(context):
        action = context.payload.get("action")
        
        if action == "analyze_goal":
            context.payload["result"] = {
                "success": True,
                "task_id": "task_001",
                "analysis": {
                    "type": "feature",
                    "scope": "medium",
                    "tags": ["authentication", "security"],
                    "description": "Implement JWT authentication"
                },
                "ethical_validation": {"approved": True},
                "message": "Task task_001 created and ready for execution"
            }
        
        elif action == "execute_mission":
            context.payload["result"] = {
                "success": True,
                "task_id": "task_001",
                "status": "analyzing",
                "plan": {
                    "task_id": "task_001",
                    "next_steps": [
                        "Formulate detailed specification",
                        "Delegate to external coding agent",
                        "Monitor progress"
                    ],
                    "estimated_phases": {
                        "specification": "Strategic planning",
                        "delegation": "External agent",
                        "validation": "QA review"
                    }
                },
                "message": "Strategic plan created"
            }
        
        return context
    
    orchestrator.execute = mock_execute
    return orchestrator


@pytest.fixture
def autonomous_interface(mock_orchestrator):
    """Create configured AutonomousInterface instance."""
    plugin = AutonomousInterface()
    plugin.setup({
        "cognitive_orchestrator": mock_orchestrator,
        "worklog_path": "test_worklog.md"
    })
    return plugin


@pytest.fixture
def sample_context():
    """Create sample SharedContext."""
    return SharedContext(
        session_id="test_session",
        user_input="autonomous: implement JWT authentication",
        current_state="INITIAL",
        logger=MagicMock(),
        payload={}
    )


class TestAutonomousInterfaceMetadata:
    """Test plugin metadata and initialization."""
    
    def test_plugin_metadata(self):
        """Verify plugin has correct metadata."""
        plugin = AutonomousInterface()
        
        assert plugin.name == "interface_autonomous"
        assert plugin.plugin_type == PluginType.INTERFACE
        assert plugin.version == "1.0.0"
    
    def test_initialization(self):
        """Verify proper initialization."""
        plugin = AutonomousInterface()
        
        assert plugin.orchestrator is None
        assert plugin.worklog_path == "WORKLOG.md"
    
    def test_setup_with_orchestrator(self, mock_orchestrator):
        """Verify setup configures orchestrator."""
        plugin = AutonomousInterface()
        plugin.setup({
            "cognitive_orchestrator": mock_orchestrator,
            "worklog_path": "custom_worklog.md"
        })
        
        assert plugin.orchestrator == mock_orchestrator
        assert plugin.worklog_path == "custom_worklog.md"
    
    def test_setup_without_orchestrator(self):
        """Verify setup handles missing orchestrator gracefully."""
        plugin = AutonomousInterface()
        plugin.setup({})
        
        assert plugin.orchestrator is None
        assert plugin.worklog_path == "WORKLOG.md"


class TestCommandDetection:
    """Test autonomous command detection."""
    
    @pytest.mark.asyncio
    async def test_detects_autonomous_command(self, autonomous_interface):
        """Verify detection of 'autonomous:' prefix."""
        context = SharedContext(
            session_id="test",
            user_input="autonomous: implement feature X",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await autonomous_interface.execute(context)
        
        # Should have autonomous_response
        assert hasattr(result_context, "autonomous_response")
        assert result_context.autonomous_response is not None
    
    @pytest.mark.asyncio
    async def test_ignores_non_autonomous_command(self, autonomous_interface):
        """Verify pass-through for non-autonomous commands."""
        context = SharedContext(
            session_id="test",
            user_input="normal user input",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await autonomous_interface.execute(context)
        
        # Should NOT have autonomous_response
        assert not hasattr(result_context, "autonomous_response") or \
               result_context.autonomous_response is None
    
    @pytest.mark.asyncio
    async def test_handles_empty_goal(self, autonomous_interface):
        """Verify error handling for empty goal."""
        context = SharedContext(
            session_id="test",
            user_input="autonomous:",  # No goal text
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await autonomous_interface.execute(context)
        
        assert hasattr(result_context, "autonomous_response")
        assert "Error: No goal specified" in result_context.autonomous_response
    
    @pytest.mark.asyncio
    async def test_handles_whitespace_goal(self, autonomous_interface):
        """Verify error handling for whitespace-only goal."""
        context = SharedContext(
            session_id="test",
            user_input="autonomous:    ",  # Only whitespace
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await autonomous_interface.execute(context)
        
        assert hasattr(result_context, "autonomous_response")
        assert "Error: No goal specified" in result_context.autonomous_response


class TestWorkflowExecution:
    """Test autonomous workflow execution."""
    
    @pytest.mark.asyncio
    async def test_successful_workflow(self, autonomous_interface, sample_context):
        """Verify successful end-to-end workflow."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            autonomous_interface.worklog_path = f.name
        
        try:
            result_context = await autonomous_interface.execute(sample_context)
            
            assert hasattr(result_context, "autonomous_response")
            assert "✅ Autonomous Mission Initiated" in result_context.autonomous_response
            assert "Task ID: task_001" in result_context.autonomous_response
            assert "Status: analyzing" in result_context.autonomous_response
        
        finally:
            Path(autonomous_interface.worklog_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_workflow_without_orchestrator(self):
        """Verify error handling when orchestrator is missing."""
        plugin = AutonomousInterface()
        plugin.setup({})  # No orchestrator
        
        context = SharedContext(
            session_id="test",
            user_input="autonomous: test goal",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await plugin.execute(context)
        
        assert hasattr(result_context, "autonomous_response")
        assert "Error: Strategic Orchestrator not available" in result_context.autonomous_response
    
    @pytest.mark.asyncio
    async def test_workflow_analysis_failure(self, mock_orchestrator):
        """Verify error handling when goal analysis fails."""
        # Modify orchestrator to return failure
        async def mock_execute_fail(context):
            if context.payload.get("action") == "analyze_goal":
                context.payload["result"] = {
                    "success": False,
                    "error": "Analysis failed",
                    "message": "Invalid goal format"
                }
            return context
        
        mock_orchestrator.execute = mock_execute_fail
        
        plugin = AutonomousInterface()
        plugin.setup({"cognitive_orchestrator": mock_orchestrator})
        
        context = SharedContext(
            session_id="test",
            user_input="autonomous: test goal",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await plugin.execute(context)
        
        assert hasattr(result_context, "autonomous_response")
        assert "Goal analysis failed" in result_context.autonomous_response
    
    @pytest.mark.asyncio
    async def test_workflow_execution_failure(self, mock_orchestrator):
        """Verify error handling when mission execution fails."""
        # Modify orchestrator to fail on execution
        async def mock_execute_fail(context):
            action = context.payload.get("action")
            
            if action == "analyze_goal":
                context.payload["result"] = {
                    "success": True,
                    "task_id": "task_001",
                    "analysis": {},
                    "ethical_validation": {"approved": True}
                }
            elif action == "execute_mission":
                context.payload["result"] = {
                    "success": False,
                    "error": "Execution failed"
                }
            
            return context
        
        mock_orchestrator.execute = mock_execute_fail
        
        plugin = AutonomousInterface()
        plugin.setup({"cognitive_orchestrator": mock_orchestrator})
        
        context = SharedContext(
            session_id="test",
            user_input="autonomous: test goal",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await plugin.execute(context)
        
        assert hasattr(result_context, "autonomous_response")
        assert "Mission execution failed" in result_context.autonomous_response


class TestWorklogUpdate:
    """Test WORKLOG.md update functionality."""
    
    @pytest.mark.asyncio
    async def test_worklog_creation(self, autonomous_interface, sample_context):
        """Verify WORKLOG.md is created if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            worklog_path = f.name
        
        # Delete the file to test creation
        Path(worklog_path).unlink()
        autonomous_interface.worklog_path = worklog_path
        
        try:
            await autonomous_interface.execute(sample_context)
            
            assert Path(worklog_path).exists()
            content = Path(worklog_path).read_text()
            assert "AUTONOMOUS MISSION: task_001" in content
        
        finally:
            Path(worklog_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_worklog_append(self, autonomous_interface, sample_context):
        """Verify WORKLOG.md entries are appended."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("# WORKLOG\n\nExisting content\n")
            worklog_path = f.name
        
        autonomous_interface.worklog_path = worklog_path
        
        try:
            await autonomous_interface.execute(sample_context)
            
            content = Path(worklog_path).read_text()
            assert "Existing content" in content
            assert "AUTONOMOUS MISSION: task_001" in content
        
        finally:
            Path(worklog_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_worklog_content_structure(self, autonomous_interface, sample_context):
        """Verify WORKLOG.md entry has correct structure."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            worklog_path = f.name
        
        autonomous_interface.worklog_path = worklog_path
        
        try:
            await autonomous_interface.execute(sample_context)
            
            content = Path(worklog_path).read_text()
            
            # Verify key sections
            assert "AUTONOMOUS MISSION: task_001" in content
            assert "**Status:** PLANNED" in content
            assert "**Goal:**" in content
            assert "**Analysis:**" in content
            assert "**Strategic Plan:**" in content
            assert "Next Steps:" in content
        
        finally:
            Path(worklog_path).unlink(missing_ok=True)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_exception_during_workflow(self, mock_orchestrator):
        """Verify graceful error handling for exceptions."""
        # Make orchestrator raise exception
        async def mock_execute_error(context):
            raise ValueError("Orchestrator error")
        
        mock_orchestrator.execute = mock_execute_error
        
        plugin = AutonomousInterface()
        plugin.setup({"cognitive_orchestrator": mock_orchestrator})
        
        context = SharedContext(
            session_id="test",
            user_input="autonomous: test goal",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        result_context = await plugin.execute(context)
        
        assert hasattr(result_context, "autonomous_response")
        assert "Error executing autonomous mission" in result_context.autonomous_response
    
    @pytest.mark.asyncio
    async def test_worklog_write_failure(self, autonomous_interface, sample_context):
        """Verify workflow continues even if WORKLOG update fails."""
        # Set invalid path
        autonomous_interface.worklog_path = "/invalid/path/worklog.md"
        
        # Should not raise exception, just log error
        result_context = await autonomous_interface.execute(sample_context)
        
        # Workflow should complete successfully
        assert hasattr(result_context, "autonomous_response")
        assert "✅ Autonomous Mission Initiated" in result_context.autonomous_response


class TestIntegration:
    """Integration tests with real-ish scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_autonomous_workflow(self, autonomous_interface):
        """Test complete workflow with realistic data."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            worklog_path = f.name
        
        autonomous_interface.worklog_path = worklog_path
        
        context = SharedContext(
            session_id="integration_test",
            user_input="autonomous: implement comprehensive user authentication with JWT tokens and refresh mechanism",
            current_state="INITIAL",
            logger=MagicMock()
        )
        
        try:
            result_context = await autonomous_interface.execute(context)
            
            # Verify response
            assert hasattr(result_context, "autonomous_response")
            response = result_context.autonomous_response
            assert "✅ Autonomous Mission Initiated" in response
            assert "task_001" in response
            
            # Verify WORKLOG
            content = Path(worklog_path).read_text()
            assert "task_001" in content
            assert "PLANNED" in content
        
        finally:
            Path(worklog_path).unlink(missing_ok=True)
