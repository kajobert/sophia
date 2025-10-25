import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from uvicorn import Config, Server
from typing import Dict
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class WebUIInterface(BasePlugin):
    """A plugin that provides a web-based chat interface via FastAPI and WebSockets."""

    def __init__(self):
        self._server_started = False

    @property
    def name(self) -> str:
        return "interface_webui"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.INTERFACE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Configures the plugin, but does not start the server."""
        self.app = FastAPI()
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 8000)
        self.connections: Dict[str, WebSocket] = {}
        self.input_queue: asyncio.Queue = asyncio.Queue()

        @self.app.get("/")
        async def get_chat_ui():
            return FileResponse("frontend/chat.html")

        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            await websocket.accept()
            self.connections[session_id] = websocket
            logger.info(f"WebUI client connected with session_id: {session_id}")
            try:
                while True:
                    data = await websocket.receive_text()

                    async def response_callback(message: str):
                        await self.send_response(session_id, message)

                    await self.input_queue.put((data, response_callback))
            except WebSocketDisconnect:
                del self.connections[session_id]
                logger.info(f"WebUI client {session_id} disconnected.")

    async def start_server(self):
        """Starts the Uvicorn server in a background task."""
        server_config = Config(self.app, host=self.host, port=self.port, log_level="info")
        server = Server(server_config)
        asyncio.create_task(server.serve())
        logger.info(f"WebUI server started at http://{self.host}:{self.port}")
        self._server_started = True

    async def execute(self, context: SharedContext) -> SharedContext:
        """Waits for user input from the WebSocket and starts the server if not already running."""
        if not self._server_started:
            await self.start_server()

        user_input, response_callback = await self.input_queue.get()
        context.user_input = user_input
        context.payload["_response_callback"] = response_callback
        return context

    async def send_response(self, session_id: str, message: str):
        """Sends a message back to a specific web client."""
        if session_id in self.connections:
            await self.connections[session_id].send_text(message)
