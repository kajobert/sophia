"""
WebSocket handler for real-time streaming.

Provides real-time updates for:
- State changes
- Log streams
- LLM thinking
- Tool execution
- Plan updates
- Budget updates
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from backend.orchestrator_manager import orchestrator_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Register event callback
        orchestrator_manager.register_event_callback(
            lambda event: self.broadcast(event)
        )
        
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """
        Send message to specific client.
        
        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending personal message: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        # Convert datetime objects to ISO format
        message = self._serialize_message(message)
        
        disconnected = set()
        
        for connection in self.active_connections:
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.add(connection)
            else:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    @staticmethod
    def _serialize_message(obj: Any) -> Any:
        """Serialize message for JSON (handle datetime, etc.)."""
        if isinstance(obj, dict):
            return {k: ConnectionManager._serialize_message(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ConnectionManager._serialize_message(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj


# Global connection manager
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time streaming.
    
    Args:
        websocket: WebSocket connection
    """
    await connection_manager.connect(websocket)
    
    try:
        # Send initial state
        initial_state = {
            "type": "initial_state",
            "timestamp": datetime.now(),
            "data": {
                "state": orchestrator_manager.get_state().model_dump(),
                "budget": orchestrator_manager.get_budget().model_dump(),
            }
        }
        await connection_manager.send_personal_message(initial_state, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message (client can send commands)
                data = await websocket.receive_json()
                
                # Handle client commands
                command = data.get("command")
                
                if command == "ping":
                    await connection_manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.now()},
                        websocket
                    )
                
                elif command == "get_state":
                    state = orchestrator_manager.get_state()
                    await connection_manager.send_personal_message(
                        {
                            "type": "state_update",
                            "timestamp": datetime.now(),
                            "data": state.model_dump()
                        },
                        websocket
                    )
                
                elif command == "get_budget":
                    budget = orchestrator_manager.get_budget()
                    await connection_manager.send_personal_message(
                        {
                            "type": "budget_update",
                            "timestamp": datetime.now(),
                            "data": budget.model_dump()
                        },
                        websocket
                    )
                
                elif command == "get_plan":
                    try:
                        plan = orchestrator_manager.get_plan()
                        await connection_manager.send_personal_message(
                            {
                                "type": "plan_update",
                                "timestamp": datetime.now(),
                                "data": plan.model_dump()
                            },
                            websocket
                        )
                    except RuntimeError as e:
                        await connection_manager.send_personal_message(
                            {
                                "type": "error",
                                "timestamp": datetime.now(),
                                "data": {"error": str(e)}
                            },
                            websocket
                        )
                
                else:
                    logger.warning(f"Unknown command: {command}")
                
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from client")
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        connection_manager.disconnect(websocket)
