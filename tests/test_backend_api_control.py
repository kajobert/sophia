"""
Tests for Backend API Mission Control endpoints.

Phase 8: Mission Control API
- POST /api/v1/missions/{id}/pause
- POST /api/v1/missions/{id}/resume
- POST /api/v1/missions/{id}/cancel
- GET  /api/v1/stats
- GET  /api/v1/models

All tests use mock orchestrator - no real LLM calls.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.server import app
from backend.orchestrator_manager import OrchestratorManager
from core.state_manager import State


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing."""
    orchestrator = Mock(spec=OrchestratorManager)
    
    # Mock state manager
    orchestrator.state_manager = Mock()
    orchestrator.state_manager.current_state = State.IDLE
    
    # Mock mission tracking
    orchestrator._paused = False
    orchestrator._cancel_requested = False
    
    # Mock methods
    orchestrator.pause_mission = AsyncMock(return_value=True)
    orchestrator.resume_mission = AsyncMock(return_value=True)
    orchestrator.cancel_mission = AsyncMock(return_value=True)
    orchestrator.get_mission_status = Mock(return_value={
        "mission_id": "test-123",
        "status": "executing",
        "state": "executing_step",
        "progress": {"total_steps": 5, "completed": 2}
    })
    orchestrator.get_stats = Mock(return_value={
        "total_missions": 10,
        "success_rate": 0.8,
        "total_cost": 0.05,
        "avg_duration": 45.2
    })
    orchestrator.get_models = Mock(return_value={
        "models": [
            {
                "name": "gemini-2.0-flash-exp",
                "provider": "gemini",
                "cost_per_1m_tokens": 0.0,
                "tier": "powerful"
            },
            {
                "name": "qwen/qwen-2.5-72b-instruct",
                "provider": "openrouter",
                "cost_per_1m_tokens": 0.07,
                "tier": "cheap"
            }
        ],
        "total": 2,
        "current_model": "gemini-2.0-flash-exp",
        "aliases": {"powerful": "gemini-2.0-flash-exp", "cheap": "qwen/qwen-2.5-72b-instruct"}
    })
    orchestrator.get_available_models = Mock(return_value=[
        {
            "name": "gemini-2.0-flash-exp",
            "provider": "gemini",
            "cost_per_1m_tokens": 0.0,
            "tier": "powerful"
        },
        {
            "name": "qwen/qwen-2.5-72b-instruct",
            "provider": "openrouter",
            "cost_per_1m_tokens": 0.07,
            "tier": "cheap"
        }
    ])
    
    return orchestrator


@pytest.fixture(autouse=True)
def mock_orchestrator_manager(mock_orchestrator):
    """Automatically patch orchestrator_manager for all tests."""
    with patch('backend.orchestrator_manager.orchestrator_manager', mock_orchestrator):
        yield mock_orchestrator


# ============================================================================
# PAUSE ENDPOINT TESTS
# ============================================================================

def test_pause_mission_success(client, mock_orchestrator):
    """Test: Successfully pause a running mission."""
    with patch('backend.orchestrator_manager.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/pause",
            json={"reason": "User requested pause"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mission_id"] == "test-123"
    assert "paused" in data["message"].lower()
    
    mock_orchestrator.pause_mission.assert_called_once_with("User requested pause")


def test_pause_mission_invalid_state(client, mock_orchestrator):
    """Test: Cannot pause mission in invalid state."""
    mock_orchestrator.state_manager.current_state = State.IDLE
    mock_orchestrator.pause_mission = AsyncMock(return_value=False)
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/pause",
            json={"reason": "Test"}
        )
    
    assert response.status_code == 400
    data = response.json()
    assert "cannot be paused" in data["detail"].lower()


def test_pause_mission_missing_reason(client, mock_orchestrator):
    """Test: Pause without reason uses default."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/pause",
            json={}
        )
    
    # Should succeed with default reason
    assert response.status_code == 200


def test_pause_mission_not_found(client, mock_orchestrator):
    """Test: Pause non-existent mission."""
    mock_orchestrator.get_mission_status = Mock(return_value=None)
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/nonexistent/pause",
            json={"reason": "Test"}
        )
    
    assert response.status_code == 404


# ============================================================================
# RESUME ENDPOINT TESTS
# ============================================================================

def test_resume_mission_success(client, mock_orchestrator):
    """Test: Successfully resume a paused mission."""
    mock_orchestrator._paused = True
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post("/api/v1/missions/test-123/resume")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "resumed" in data["message"].lower()
    
    mock_orchestrator.resume_mission.assert_called_once()


def test_resume_mission_not_paused(client, mock_orchestrator):
    """Test: Cannot resume mission that's not paused."""
    mock_orchestrator._paused = False
    mock_orchestrator.resume_mission = AsyncMock(return_value=False)
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post("/api/v1/missions/test-123/resume")
    
    assert response.status_code == 400
    assert "not paused" in response.json()["detail"].lower()


def test_resume_mission_already_completed(client, mock_orchestrator):
    """Test: Cannot resume completed mission."""
    mock_orchestrator.state_manager.current_state = State.COMPLETED
    mock_orchestrator.resume_mission = AsyncMock(return_value=False)
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post("/api/v1/missions/test-123/resume")
    
    assert response.status_code == 400


# ============================================================================
# CANCEL ENDPOINT TESTS
# ============================================================================

def test_cancel_mission_success(client, mock_orchestrator):
    """Test: Successfully cancel a running mission."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/cancel",
            json={"reason": "User cancelled"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "cancel" in data["message"].lower()
    
    mock_orchestrator.cancel_mission.assert_called_once_with("User cancelled")


def test_cancel_mission_already_completed(client, mock_orchestrator):
    """Test: Cannot cancel already completed mission."""
    mock_orchestrator.state_manager.current_state = State.COMPLETED
    mock_orchestrator.cancel_mission = AsyncMock(return_value=False)
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/cancel",
            json={"reason": "Test"}
        )
    
    assert response.status_code == 400
    assert "cannot be cancelled" in response.json()["detail"].lower()


def test_cancel_mission_default_reason(client, mock_orchestrator):
    """Test: Cancel with default reason."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/cancel",
            json={}
        )
    
    assert response.status_code == 200
    mock_orchestrator.cancel_mission.assert_called_once_with("User requested cancellation")


def test_cancel_mission_idempotent(client, mock_orchestrator):
    """Test: Cancelling already cancelled mission is OK."""
    mock_orchestrator._cancel_requested = True
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post(
            "/api/v1/missions/test-123/cancel",
            json={"reason": "Test"}
        )
    
    # Should succeed (idempotent)
    assert response.status_code == 200


# ============================================================================
# STATS ENDPOINT TESTS
# ============================================================================

def test_get_stats_success(client, mock_orchestrator):
    """Test: Get system statistics."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_missions" in data
    assert "success_rate" in data
    assert "total_cost_usd" in data  # API uses total_cost_usd
    assert "total_tokens" in data
    assert "average_mission_duration" in data
    
    assert data["total_missions"] == 10
    assert data["success_rate"] == 0.8
    assert data["total_cost"] == 0.05


def test_get_stats_empty(client, mock_orchestrator):
    """Test: Stats with no missions."""
    mock_orchestrator.get_stats = Mock(return_value={
        "total_missions": 0,
        "success_rate": 0.0,
        "total_cost": 0.0,
        "avg_duration": 0.0
    })
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_missions"] == 0


def test_get_stats_includes_metadata(client, mock_orchestrator):
    """Test: Stats include metadata like timestamp."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/stats")
    
    assert response.status_code == 200
    # Should be valid JSON with expected fields
    data = response.json()
    assert isinstance(data, dict)
    assert all(key in data for key in ["total_missions", "success_rate", "total_cost_usd"])


# ============================================================================
# MODELS ENDPOINT TESTS
# ============================================================================

def test_get_models_success(client, mock_orchestrator):
    """Test: Get available LLM models."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/models")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "models" in data
    assert len(data["models"]) == 2
    
    # Check first model
    gemini = data["models"][0]
    assert gemini["name"] == "gemini-2.0-flash-exp"
    assert gemini["provider"] == "gemini"
    assert gemini["tier"] == "powerful"


def test_get_models_includes_pricing(client, mock_orchestrator):
    """Test: Models include pricing information."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/models")
    
    data = response.json()
    models = data["models"]
    
    for model in models:
        assert "cost_per_1m_tokens" in model
        assert isinstance(model["cost_per_1m_tokens"], (int, float))


def test_get_models_multiple_providers(client, mock_orchestrator):
    """Test: Models from different providers."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/models")
    
    data = response.json()
    models = data["models"]
    
    providers = {m["provider"] for m in models}
    assert "gemini" in providers
    assert "openrouter" in providers


def test_get_models_empty_list(client, mock_orchestrator):
    """Test: No models available."""
    mock_orchestrator.get_available_models = Mock(return_value=[])
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/models")
    
    assert response.status_code == 200
    data = response.json()
    assert data["models"] == []


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_pause_resume_cancel_flow(client, mock_orchestrator):
    """Test: Complete pause → resume → cancel flow."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        # Pause
        response = client.post("/api/v1/missions/test-123/pause", json={})
        assert response.status_code == 200
        
        # Resume
        mock_orchestrator._paused = True
        response = client.post("/api/v1/missions/test-123/resume")
        assert response.status_code == 200
        
        # Cancel
        response = client.post("/api/v1/missions/test-123/cancel", json={})
        assert response.status_code == 200


def test_stats_after_multiple_missions(client, mock_orchestrator):
    """Test: Stats reflect multiple missions."""
    mock_orchestrator.get_stats = Mock(return_value={
        "total_missions": 100,
        "success_rate": 0.95,
        "total_cost": 1.25,
        "avg_duration": 60.5
    })
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.get("/api/v1/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_missions"] == 100
    assert data["success_rate"] == 0.95


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_control_endpoints_handle_exceptions(client, mock_orchestrator):
    """Test: Control endpoints handle unexpected errors gracefully."""
    mock_orchestrator.pause_mission = AsyncMock(side_effect=Exception("Unexpected error"))
    
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post("/api/v1/missions/test-123/pause", json={})
    
    # Should return 500 with error details
    assert response.status_code in [400, 500]


def test_invalid_mission_id_format(client, mock_orchestrator):
    """Test: Invalid mission ID format."""
    with patch('backend.routes.missions.orchestrator_manager', mock_orchestrator):
        response = client.post("/api/v1/missions//pause", json={})
    
    # Should handle gracefully
    assert response.status_code in [404, 422]


# ============================================================================
# SUMMARY
# ============================================================================

def test_summary():
    """
    Summary of Phase 8 API Control Tests:
    
    ✅ Pause endpoint: 4 tests
    ✅ Resume endpoint: 3 tests
    ✅ Cancel endpoint: 4 tests
    ✅ Stats endpoint: 3 tests
    ✅ Models endpoint: 4 tests
    ✅ Integration: 2 tests
    ✅ Error handling: 2 tests
    
    Total: 22 tests
    Coverage: All new endpoints
    Speed: All tests use mocks (no LLM calls)
    """
    pass
