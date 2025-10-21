"""
WebSocket handler for Sophia Chat.
"""
import logging
from fastapi import WebSocket, WebSocketDisconnect
from backend.sophia_chat_core import SophiaChatCore

logger = logging.getLogger(__name__)

async def handle_websocket_connection(websocket: WebSocket, session_id: str, sophia_chat_core: SophiaChatCore):
    """
    Handles the WebSocket connection for a chat session.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            user_message = await websocket.receive_text()
            logger.info(f"Received message from {session_id}: {user_message}")

            # Get the response from Sophia's core
            assistant_response = await sophia_chat_core.handle_message(session_id, user_message)

            # Send the response back to the client
            await websocket.send_text(assistant_response)
            logger.info(f"Sent response to {session_id}: {assistant_response}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"An error occurred in the WebSocket handler for session {session_id}: {e}", exc_info=True)
        # Optionally, send an error message to the client
        await websocket.send_text(f"An error occurred: {e}")
    finally:
        # No need to manually close, FastAPI handles it.
        pass
