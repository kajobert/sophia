"""
End-to-End Integration Test for Autonomous Workflow

Tests the complete autonomous development workflow from goal input
through analysis, planning, and WORKLOG documentation.

This test validates:
1. HKA layer integration (INSTINKTY, PODVĚDOMÍ, VĚDOMÍ)
2. Plugin dependency injection and communication
3. Autonomous mission trigger mechanism
4. WORKLOG automation
5. Error handling and recovery
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from core.kernel import Kernel
from core.context import SharedContext


class TestAutonomousWorkflowE2E:
    """End-to-end tests for autonomous development workflow."""
    
    @pytest.fixture
    def mock_plugins(self):
        """Create mock plugins for testing."""
        # Mock NotesAnalyzer (PODVĚDOMÍ)
        mock_notes_analyzer = Mock()
        mock_notes_analyzer.name = "cognitive_notes_analyzer"
        mock_notes_analyzer.execute = AsyncMock(return_value=SharedContext(
            session_id="test",
            user_input="",
            current_state="analyzing",
            logger=Mock(),
            payload={
                "result": [{
                    "raw_idea": "Create a weather plugin",
                    "formulated_goal": "Implement a plugin that fetches weather data using wttr.in API",
                    "feasibility": "high",
                    "alignment_with_dna": {
                        "ahimsa": True,
                        "satya": True,
                        "kaizen": True
                    },
                    "context": {
                        "relevant_docs": [],
                        "similar_missions": [],
                        "existing_plugins": []
                    }
                }]
            }
        ))
        
        # Mock EthicalGuardian (INSTINKTY)
        mock_ethical_guardian = Mock()
        mock_ethical_guardian.name = "cognitive_ethical_guardian"
        mock_ethical_guardian.execute = AsyncMock(return_value=SharedContext(
            session_id="test",
            user_input="",
            current_state="validating",
            logger=Mock(),
            payload={
                "result": {
                    "approved": True,
                    "concerns": [],
                    "recommendation": "Goal is ethically sound"
                }
            }
        ))
        
        # Mock TaskManager (PODVĚDOMÍ)
        mock_task_manager = Mock()
        mock_task_manager.name = "cognitive_task_manager"
        
        call_count = {"count": 0}
        
        async def task_manager_execute(context):
            action = context.payload.get("action")
            call_count["count"] += 1
            
            if action == "create_task":
                context.payload["result"] = f"task-test-{call_count['count']}"
            elif action == "get_task":
                context.payload["result"] = {
                    "task_id": context.payload.get("task_id"),
                    "goal": {
                        "formulated_goal": "Test goal",
                        "feasibility": "high"
                    },
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "history": []
                }
            elif action == "get_similar_tasks":
                context.payload["result"] = []
            elif action == "update_task":
                context.payload["result"] = True
            
            return context
        
        mock_task_manager.execute = task_manager_execute
        
        # Mock Orchestrator (VĚDOMÍ)
        mock_orchestrator = Mock()
        mock_orchestrator.name = "cognitive_orchestrator"
        mock_orchestrator.task_manager = mock_task_manager
        mock_orchestrator.notes_analyzer = mock_notes_analyzer
        mock_orchestrator.ethical_guardian = mock_ethical_guardian
        
        async def orchestrator_execute(context):
            action = context.payload.get("action")
            
            if action == "analyze_goal":
                # Simulate goal analysis
                goal_text = context.payload.get("goal", "")
                
                # Call notes analyzer
                analysis_ctx = SharedContext(
                    session_id=context.session_id,
                    user_input=goal_text,
                    current_state="analyzing",
                    logger=context.logger,
                    payload={"goals": [goal_text]}
                )
                analysis_ctx = await mock_notes_analyzer.execute(analysis_ctx)
                analysis = analysis_ctx.payload.get("result", [])[0]
                
                # Call ethical guardian
                ethics_ctx = SharedContext(
                    session_id=context.session_id,
                    user_input=goal_text,
                    current_state="validating",
                    logger=context.logger,
                    payload={"action": "validate_goal", "goal": analysis}
                )
                ethics_ctx = await mock_ethical_guardian.execute(ethics_ctx)
                ethical_validation = ethics_ctx.payload.get("result", {})
                
                if not ethical_validation.get("approved"):
                    context.payload["result"] = {
                        "success": False,
                        "message": "Goal rejected due to ethical concerns"
                    }
                    return context
                
                # Create task
                task_ctx = SharedContext(
                    session_id=context.session_id,
                    user_input=goal_text,
                    current_state="creating_task",
                    logger=context.logger,
                    payload={
                        "action": "create_task",
                        "goal": analysis,
                        "context": {"ethical_validation": ethical_validation}
                    }
                )
                task_ctx = await mock_task_manager.execute(task_ctx)
                task_id = task_ctx.payload.get("result")
                
                context.payload["result"] = {
                    "success": True,
                    "task_id": task_id,
                    "analysis": analysis,
                    "ethical_validation": ethical_validation,
                    "message": f"Task {task_id} created"
                }
            
            elif action == "execute_mission":
                task_id = context.payload.get("task_id")
                
                # Get task
                get_ctx = SharedContext(
                    session_id=context.session_id,
                    user_input="",
                    current_state="loading_task",
                    logger=context.logger,
                    payload={"action": "get_task", "task_id": task_id}
                )
                get_ctx = await mock_task_manager.execute(get_ctx)
                task = get_ctx.payload.get("result")
                
                # Update status
                update_ctx = SharedContext(
                    session_id=context.session_id,
                    user_input="",
                    current_state="updating_task",
                    logger=context.logger,
                    payload={
                        "action": "update_task",
                        "task_id": task_id,
                        "status": "analyzing",
                        "notes": "Strategic analysis"
                    }
                )
                await mock_task_manager.execute(update_ctx)
                
                # Create plan
                plan = {
                    "task_id": task_id,
                    "goal": task.get("goal", {}),
                    "context": {"similar_tasks_found": 0},
                    "next_steps": [
                        "Formulate specification",
                        "Delegate to agent",
                        "Validate results"
                    ],
                    "estimated_phases": {
                        "specification": "Planning",
                        "delegation": "Not yet implemented",
                        "validation": "QA review"
                    }
                }
                
                context.payload["result"] = {
                    "success": True,
                    "task_id": task_id,
                    "status": "analyzing",
                    "plan": plan,
                    "message": "Strategic plan created"
                }
            
            return context
        
        mock_orchestrator.execute = orchestrator_execute
        
        return {
            "cognitive_orchestrator": mock_orchestrator,
            "cognitive_notes_analyzer": mock_notes_analyzer,
            "cognitive_ethical_guardian": mock_ethical_guardian,
            "cognitive_task_manager": mock_task_manager
        }
    
    @pytest.mark.asyncio
    async def test_autonomous_workflow_success(self, mock_plugins, tmp_path):
        """Test successful autonomous workflow from goal to WORKLOG."""
        # Setup
        kernel = Kernel()
        
        # Mock WORKLOG path
        test_worklog = tmp_path / "WORKLOG.md"
        test_worklog.write_text("# Test Worklog\n\n")
        
        with patch('core.kernel.Path') as mock_path:
            mock_path.return_value = test_worklog
            
            context = SharedContext(
                session_id="test_autonomous",
                user_input="",
                current_state="AUTONOMOUS",
                logger=Mock()
            )
            
            # Execute autonomous mission
            result = await kernel.trigger_autonomous_mission(
                goal_text="Create a weather plugin",
                context=context,
                all_plugins_map=mock_plugins
            )
        
        # Verify
        assert "✅ Autonomous Mission Initiated" in result
        assert "Task ID: task-test-1" in result
        assert "Next Steps:" in result
        assert "Formulate specification" in result
        
        # Verify plugins were called
        assert mock_plugins["cognitive_notes_analyzer"].execute.called
        assert mock_plugins["cognitive_ethical_guardian"].execute.called
    
    @pytest.mark.asyncio
    async def test_autonomous_workflow_ethical_rejection(self, mock_plugins):
        """Test workflow when goal is ethically rejected."""
        # Setup - modify ethical guardian to reject
        mock_plugins["cognitive_ethical_guardian"].execute = AsyncMock(
            return_value=SharedContext(
                session_id="test",
                user_input="",
                current_state="validating",
                logger=Mock(),
                payload={
                    "result": {
                        "approved": False,
                        "concerns": ["Potential harm to users"],
                        "recommendation": "Reject this goal"
                    }
                }
            )
        )
        
        kernel = Kernel()
        context = SharedContext(
            session_id="test_reject",
            user_input="",
            current_state="AUTONOMOUS",
            logger=Mock()
        )
        
        # Execute
        result = await kernel.trigger_autonomous_mission(
            goal_text="Create a malicious plugin",
            context=context,
            all_plugins_map=mock_plugins
        )
        
        # Verify rejection
        assert "Goal analysis failed" in result
        assert "ethical concerns" in result
    
    @pytest.mark.asyncio
    async def test_autonomous_workflow_missing_orchestrator(self):
        """Test error handling when orchestrator is missing."""
        kernel = Kernel()
        context = SharedContext(
            session_id="test_missing",
            user_input="",
            current_state="AUTONOMOUS",
            logger=Mock()
        )
        
        # Execute with empty plugin map
        result = await kernel.trigger_autonomous_mission(
            goal_text="Test goal",
            context=context,
            all_plugins_map={}
        )
        
        # Verify error message
        assert "Error: Strategic Orchestrator not available" in result
    
    @pytest.mark.asyncio
    async def test_autonomous_workflow_execution_failure(self, mock_plugins):
        """Test error handling during mission execution."""
        # Setup - make execution fail
        original_execute = mock_plugins["cognitive_orchestrator"].execute
        
        async def failing_execute(context):
            action = context.payload.get("action")
            
            if action == "execute_mission":
                context.payload["result"] = {
                    "success": False,
                    "error": "Execution error"
                }
                return context
            else:
                # Let analyze_goal succeed
                return await original_execute(context)
        
        mock_plugins["cognitive_orchestrator"].execute = failing_execute
        
        kernel = Kernel()
        context = SharedContext(
            session_id="test_fail",
            user_input="",
            current_state="AUTONOMOUS",
            logger=Mock()
        )
        
        # Execute
        result = await kernel.trigger_autonomous_mission(
            goal_text="Test goal",
            context=context,
            all_plugins_map=mock_plugins
        )
        
        # Verify error is reported
        assert "Mission execution failed" in result
    
    @pytest.mark.asyncio
    async def test_worklog_update(self, mock_plugins, tmp_path):
        """Test that WORKLOG.md is correctly updated."""
        kernel = Kernel()
        
        # Create test WORKLOG
        test_worklog = tmp_path / "WORKLOG.md"
        test_worklog.write_text("# Test Worklog\n\n")
        
        # Execute with mocked Path
        with patch.object(Path, '__new__', return_value=test_worklog):
            await kernel._update_worklog_autonomous(
                task_id="task-123",
                goal="Create a weather plugin",
                analysis={
                    "formulated_goal": "Implement weather plugin with wttr.in",
                    "feasibility": "high",
                    "alignment_with_dna": {
                        "ahimsa": True,
                        "satya": True,
                        "kaizen": True
                    }
                },
                plan={
                    "next_steps": ["Step 1", "Step 2"],
                    "context": {"similar_tasks_found": 2},
                    "estimated_phases": {
                        "specification": "Planning",
                        "delegation": "External agent"
                    }
                },
                status="PLANNED"
            )
        
        # Verify WORKLOG content
        content = test_worklog.read_text()
        assert "## Autonomous Mission:" in content
        assert "task-123" in content
        assert "Create a weather plugin" in content
        assert "DNA Alignment:" in content
        assert "Ahimsa (Non-harm): True" in content
        assert "Next Steps:" in content
        assert "Step 1" in content
        assert "Similar tasks found: 2" in content
        assert "PLANNED" in content
    
    def test_autonomous_trigger_format(self):
        """Test that autonomous trigger format is correctly detected."""
        test_inputs = [
            ("autonomous: Create plugin", True, "Create plugin"),
            ("autonomous:Test", True, "Test"),
            ("autonomous:   Spaces   ", True, "Spaces"),
            ("regular input", False, None),
            ("auto: not autonomous", False, None)
        ]
        
        for input_text, should_trigger, expected_goal in test_inputs:
            is_autonomous = input_text.startswith("autonomous:")
            if is_autonomous:
                goal = input_text[11:].strip()
                assert goal == expected_goal
            else:
                assert not should_trigger

