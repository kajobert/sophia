"""Hybrid Dashboard Server - Minimal Sophia with OpenRouter LLM

For Jules VM testing with REAL interaction capabilities:
- ✅ Uses OpenRouter API (no local Ollama needed)
- ✅ WebSocket support (real-time chat)
- ✅ Minimal Sophia kernel (only essential plugins)
- ✅ SQLite databases (real task queue)
- ⚠️ NO cognitive plugins (too complex for Jules VM)

Jules provides OpenRouter API key via environment variable:
    export OPENROUTER_API_KEY="sk-or-..."

Usage:
    python scripts/dashboard_server_hybrid.py

Then test with Playwright:
    pytest tests/e2e/test_dashboard.py --headed
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
import json
import sqlite3
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from uvicorn import Config, Server
from typing import Dict

# ============================================
# MINIMAL SOPHIA KERNEL (OpenRouter only)
# ============================================

class SimpleOpenRouterLLM:
    """Simple OpenRouter LLM client - NO Ollama needed."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "deepseek/deepseek-chat"  # Cheap: $0.14/1M tokens
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
    async def chat(self, user_message: str) -> str:
        """Send message to OpenRouter LLM, return response."""
        import httpx
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/ShotyCZ/sophia",
            "X-Title": "SOPHIA AMI Testing",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are SOPHIA, an autonomous AGI kernel. Answer user questions concisely and helpfully."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            return f"❌ LLM Error: {str(e)}"


class MinimalTaskQueue:
    """Simple SQLite task queue."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Create tasks table if not exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_at TEXT,
                updated_at TEXT,
                result TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def add_task(self, description: str, priority: str = "medium"):
        """Add task to queue."""
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO tasks (description, status, priority, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (description, "completed", priority, now, now)
        )
        conn.commit()
        conn.close()
        
    def get_tasks(self, limit: int = 20, offset: int = 0):
        """Get tasks from queue."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        tasks = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute("SELECT COUNT(*) as total FROM tasks")
        total = cursor.fetchone()["total"]
        
        conn.close()
        
        return {"tasks": tasks, "total": total}


# ============================================
# HYBRID DASHBOARD SERVER
# ============================================

class HybridDashboardServer:
    """Minimal dashboard server with OpenRouter LLM."""
    
    def __init__(self, api_key: str):
        self.app = FastAPI()
        self.llm = SimpleOpenRouterLLM(api_key)
        self.task_queue = MinimalTaskQueue(Path(".data/tasks.sqlite"))
        self.connections: Dict[str, WebSocket] = {}
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        # Static pages
        @self.app.get("/")
        async def root():
            return {"message": "SOPHIA Hybrid Dashboard", "dashboard": "/dashboard"}
        
        @self.app.get("/dashboard")
        async def dashboard():
            dashboard_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
            return FileResponse(str(dashboard_path))
        
        # WebSocket for real-time chat
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            await websocket.accept()
            self.connections[session_id] = websocket
            
            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "response",
                "message": "🤖 SOPHIA Hybrid Mode - Connected! Using OpenRouter LLM (DeepSeek)."
            }))
            
            try:
                while True:
                    data = await websocket.receive_text()
                    
                    # Parse message
                    try:
                        msg_data = json.loads(data)
                        user_message = msg_data.get("message", data)
                    except json.JSONDecodeError:
                        user_message = data
                    
                    # Add to task queue
                    self.task_queue.add_task(f"Chat: {user_message[:100]}")
                    
                    # Send "thinking" message
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "message": "🤔 Thinking..."
                    }))
                    
                    # Get LLM response
                    llm_response = await self.llm.chat(user_message)
                    
                    # Send response
                    await websocket.send_text(json.dumps({
                        "type": "response",
                        "message": llm_response
                    }))
                    
            except WebSocketDisconnect:
                if session_id in self.connections:
                    del self.connections[session_id]
        
        # API endpoints
        @self.app.get("/api/tasks")
        async def get_tasks(limit: int = 20, offset: int = 0):
            return self.task_queue.get_tasks(limit, offset)
        
        @self.app.get("/api/stats")
        async def get_stats():
            tasks_data = self.task_queue.get_tasks(limit=1000)
            tasks = tasks_data["tasks"]
            
            return {
                "plugin_count": 1,  # Only LLM plugin
                "pending_count": len([t for t in tasks if t["status"] == "pending"]),
                "done_count": len([t for t in tasks if t["status"] in ["completed", "done"]]),
                "failed_count": len([t for t in tasks if t["status"] == "failed"]),
            }
        
        @self.app.get("/api/hypotheses")
        async def get_hypotheses(limit: int = 20):
            # Return empty list - no cognitive plugins
            return {
                "hypotheses": [],
                "total": 0,
                "message": "Hybrid mode: No cognitive plugins loaded"
            }
        
        @self.app.get("/api/benchmarks")
        async def get_benchmarks(limit: int = 100):
            # Return empty list - no benchmarking
            return {
                "benchmarks": [],
                "total": 0,
                "message": "Hybrid mode: No benchmarking plugins loaded"
            }
        
        @self.app.get("/api/logs")
        async def get_logs(limit: int = 100):
            # Return minimal logs
            return {
                "logs": [
                    {
                        "id": 1,
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "source": "hybrid_server",
                        "message": "Dashboard server started in hybrid mode"
                    },
                    {
                        "id": 2,
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "source": "openrouter_llm",
                        "message": "Using OpenRouter API with DeepSeek model"
                    }
                ],
                "total": 2
            }
        
        @self.app.post("/api/tools/{tool_name}")
        async def execute_tool(tool_name: str):
            return {
                "success": False,
                "message": f"Hybrid mode: Tool plugins not available ({tool_name})"
            }
    
    async def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Start the server."""
        config = Config(self.app, host=host, port=port, log_level="info")
        server = Server(config)
        await server.serve()


# ============================================
# MAIN
# ============================================

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("hybrid_dashboard")
    
    # Check for OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("=" * 60)
        logger.error("❌ ERROR: OPENROUTER_API_KEY not set!")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Please set environment variable:")
        logger.error("  export OPENROUTER_API_KEY='sk-or-v1-...'")
        logger.error("")
        logger.error("Get your API key from: https://openrouter.ai/keys")
        logger.error("=" * 60)
        return
    
    logger.info("=" * 60)
    logger.info("🚀 SOPHIA Dashboard Server - HYBRID MODE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📊 Dashboard: http://127.0.0.1:8000/dashboard")
    logger.info("💬 Chat: WebSocket enabled (real-time)")
    logger.info("🤖 LLM: OpenRouter API (DeepSeek - $0.14/1M tokens)")
    logger.info("📦 Features:")
    logger.info("   ✅ Real-time chat with LLM")
    logger.info("   ✅ Task queue (SQLite)")
    logger.info("   ✅ WebSocket support")
    logger.info("   ✅ API endpoints")
    logger.info("   ⚠️  No cognitive plugins (simplified)")
    logger.info("   ⚠️  No Ollama needed")
    logger.info("")
    logger.info("🔑 API Key: " + api_key[:20] + "..." + api_key[-10:])
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    server = HybridDashboardServer(api_key)
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Hybrid dashboard server stopped")

