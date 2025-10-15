"""
API Client for Nomad TUI.

HTTP + WebSocket client for communication with Nomad Backend API.
Provides async methods for all API endpoints and real-time event streaming.
"""

import asyncio
import json
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import logging

import httpx
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class NomadAPIClient:
    """
    Async client for Nomad Backend API.
    
    Features:
    - HTTP client for REST API
    - WebSocket client for real-time streaming
    - Event callbacks for live updates
    - Auto-reconnect on disconnect
    - Error handling & retries
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        ws_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for HTTP API
            ws_url: WebSocket URL (default: ws://localhost:8080/ws)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.ws_url = ws_url or self.base_url.replace("http", "ws") + "/ws"
        self.timeout = timeout
        
        # HTTP client
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )
        
        # WebSocket
        self.ws = None
        self.ws_task = None
        self.ws_connected = False
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            "state_update": [],
            "log_stream": [],
            "llm_thinking": [],
            "tool_execution": [],
            "plan_update": [],
            "budget_update": [],
            "error": [],
        }
    
    # ========================================================================
    # HTTP API Methods
    # ========================================================================
    
    async def get_api_info(self) -> Dict[str, Any]:
        """Get API information."""
        response = await self.http_client.get("/api/v1")
        response.raise_for_status()
        return response.json()
    
    async def create_mission(
        self,
        description: str,
        max_steps: int = 50,
        budget_limit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create and start a new mission.
        
        Args:
            description: Mission description/goal
            max_steps: Maximum steps
            budget_limit: Budget limit in USD
        
        Returns:
            Mission details
        """
        response = await self.http_client.post(
            "/api/v1/missions",
            json={
                "description": description,
                "max_steps": max_steps,
                "budget_limit": budget_limit,
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_mission_status(self) -> Dict[str, Any]:
        """Get current mission status."""
        response = await self.http_client.get("/api/v1/missions/current")
        response.raise_for_status()
        return response.json()
    
    async def list_missions(self) -> Dict[str, Any]:
        """List all missions."""
        response = await self.http_client.get("/api/v1/missions")
        response.raise_for_status()
        return response.json()
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current orchestrator state."""
        response = await self.http_client.get("/api/v1/state")
        response.raise_for_status()
        return response.json()
    
    async def get_plan(self) -> Dict[str, Any]:
        """Get current mission plan."""
        response = await self.http_client.get("/api/v1/plan")
        response.raise_for_status()
        return response.json()
    
    async def get_budget(self) -> Dict[str, Any]:
        """Get budget information."""
        response = await self.http_client.get("/api/v1/budget")
        response.raise_for_status()
        return response.json()
    
    async def get_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get logs with optional filtering.
        
        Args:
            level: Filter by log level (debug, info, warning, error, critical)
            source: Filter by source
            limit: Maximum number of logs
        
        Returns:
            Log entries
        """
        params = {"limit": limit}
        if level:
            params["level"] = level
        if source:
            params["source"] = source
        
        response = await self.http_client.get("/api/v1/logs", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        response = await self.http_client.get("/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    async def ping(self) -> Dict[str, Any]:
        """Simple ping for uptime check."""
        response = await self.http_client.get("/api/v1/health/ping")
        response.raise_for_status()
        return response.json()
    
    # ========================================================================
    # WebSocket Methods
    # ========================================================================
    
    def on_event(self, event_type: str, callback: Callable) -> None:
        """
        Register callback for WebSocket events.
        
        Args:
            event_type: Event type (state_update, log_stream, etc.)
            callback: Async callback function
        
        Example:
            async def on_state_change(data):
                print(f"State: {data['state']}")
            
            client.on_event("state_update", on_state_change)
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    async def connect_websocket(self) -> None:
        """Connect to WebSocket and start listening."""
        if self.ws_task and not self.ws_task.done():
            logger.warning("WebSocket already connected")
            return
        
        self.ws_task = asyncio.create_task(self._websocket_loop())
        logger.info("WebSocket connection started")
    
    async def disconnect_websocket(self) -> None:
        """Disconnect from WebSocket."""
        if self.ws_task:
            self.ws_task.cancel()
            try:
                await self.ws_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            await self.ws.close()
        
        self.ws_connected = False
        logger.info("WebSocket disconnected")
    
    async def _websocket_loop(self) -> None:
        """WebSocket connection loop with auto-reconnect."""
        retry_delay = 1.0
        max_retry_delay = 30.0
        
        while True:
            try:
                async with ws_connect(self.ws_url) as websocket:
                    self.ws = websocket
                    self.ws_connected = True
                    retry_delay = 1.0  # Reset retry delay on successful connect
                    
                    logger.info(f"WebSocket connected to {self.ws_url}")
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._handle_ws_message(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from WebSocket: {e}")
                        except Exception as e:
                            logger.error(f"Error handling WebSocket message: {e}")
            
            except ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.ws_connected = False
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.ws_connected = False
            
            # Auto-reconnect with exponential backoff
            logger.info(f"Reconnecting in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_retry_delay)
    
    async def _handle_ws_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        event_type = data.get("type")
        event_data = data.get("data", {})
        
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    await callback(event_data)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
        else:
            logger.debug(f"Unhandled event type: {event_type}")
    
    async def ws_send_command(self, command: str, **kwargs) -> None:
        """
        Send command to WebSocket server.
        
        Args:
            command: Command name (ping, get_state, get_budget, get_plan)
            **kwargs: Additional command arguments
        """
        if not self.ws or not self.ws_connected:
            logger.warning("WebSocket not connected, cannot send command")
            return
        
        message = {
            "command": command,
            **kwargs
        }
        
        await self.ws.send(json.dumps(message))
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    async def is_backend_alive(self) -> bool:
        """Check if backend is reachable."""
        try:
            await self.ping()
            return True
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close all connections."""
        await self.disconnect_websocket()
        await self.http_client.aclose()
        logger.info("API client closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_client(
    base_url: str = "http://localhost:8080",
    connect_ws: bool = True,
) -> NomadAPIClient:
    """
    Create and initialize API client.
    
    Args:
        base_url: Base URL for API
        connect_ws: Whether to connect WebSocket immediately
    
    Returns:
        Initialized API client
    """
    client = NomadAPIClient(base_url=base_url)
    
    # Check if backend is alive
    if not await client.is_backend_alive():
        raise ConnectionError(f"Backend not reachable at {base_url}")
    
    # Connect WebSocket if requested
    if connect_ws:
        await client.connect_websocket()
    
    return client
