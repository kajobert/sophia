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
from typing import Dict, List, Optional

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
        self._start_time = datetime.utcnow()
        self._provider_stats = {
            "openrouter": {
                "name": "openrouter",
                "mode": "online",
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
            }
        }
        self._total_calls = 0
        self._total_failures = 0
        self._total_prompt = 0
        self._total_completion = 0
        self._total_cost = 0.0
        self._last_call_at: Optional[datetime] = None
        self._mode_counts = {"online": 0, "offline": 0, "hybrid": 0}
        self._mode_tokens = {"online": 0, "offline": 0, "hybrid": 0}
        self._recent_events: List[Dict[str, str]] = []
        
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
                    self._handle_llm_result(user_message, llm_response)
                    
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

            telemetry_payload = self._build_telemetry_snapshot()

            return {
                "plugin_count": 1,  # Only LLM plugin
                "pending_count": len([t for t in tasks if t["status"] == "pending"]),
                "done_count": len([t for t in tasks if t["status"] in ["completed", "done"]]),
                "failed_count": len([t for t in tasks if t["status"] == "failed"]),
                "total_calls": telemetry_payload.get("total_calls", 0),
                "total_tokens_sent": telemetry_payload.get("total_tokens_prompt", 0),
                "total_tokens_received": telemetry_payload.get("total_tokens_completion", 0),
                "total_errors": telemetry_payload.get("total_failures", 0),
                "local_calls": telemetry_payload.get("offline_calls", 0),
                "local_tokens": telemetry_payload.get("offline_tokens", 0),
                "online_calls": telemetry_payload.get("online_calls", 0),
                "online_tokens": telemetry_payload.get("online_tokens", 0),
                "current_action": telemetry_payload.get("phase_detail", "Idle"),
                "telemetry": telemetry_payload,
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

        @self.app.get("/api/telemetry")
        async def api_telemetry():
            return self._build_telemetry_snapshot()

    def _estimate_tokens(self, text: str) -> int:
        return max(len(text.split()) * 3, 1)

    def _push_event(self, level: str, message: str, source: str) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "source": source,
        }
        self._recent_events.append(entry)
        self._recent_events = self._recent_events[-25:]

    def _record_llm_usage(self, provider: str, prompt_tokens: int, completion_tokens: int) -> None:
        stats = self._provider_stats.setdefault(
            provider,
            {
                "name": provider,
                "mode": "online",
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
            },
        )
        stats["calls"] += 1
        stats["prompt_tokens"] += prompt_tokens
        stats["completion_tokens"] += completion_tokens

        token_cost = (prompt_tokens + completion_tokens) * 0.14 / 1_000_000
        stats["cost_usd"] += token_cost

        self._total_calls += 1
        self._total_prompt += prompt_tokens
        self._total_completion += completion_tokens
        self._total_cost += token_cost
        self._last_call_at = datetime.utcnow()
        self._mode_counts["online"] += 1
        self._mode_tokens["online"] += prompt_tokens + completion_tokens

    def _handle_llm_result(self, prompt: str, completion: str) -> None:
        prompt_tokens = self._estimate_tokens(prompt)
        completion_tokens = self._estimate_tokens(completion)

        if completion.startswith("❌"):
            self._total_failures += 1
            self._push_event("error", completion[:120], "openrouter_llm")
            return

        self._record_llm_usage("openrouter", prompt_tokens, completion_tokens)
        self._push_event("info", "LLM call completed", "openrouter_llm")

    def _build_telemetry_snapshot(self) -> Dict[str, object]:
        now = datetime.utcnow()
        tasks_data = self.task_queue.get_tasks(limit=50)
        telemetry_tasks = [
            {
                "task_id": str(task.get("id")),
                "name": task.get("description", "task"),
                "status": task.get("status", "pending"),
                "source": "task_queue",
                "priority": task.get("priority"),
                "worker_id": None,
                "duration": None,
                "started_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
            }
            for task in tasks_data.get("tasks", [])[:10]
        ]

        provider_stats = [
            {
                **stats,
                "total_tokens": stats["prompt_tokens"] + stats["completion_tokens"],
            }
            for stats in self._provider_stats.values()
        ]

        return {
            "generated_at": now.isoformat(),
            "uptime_seconds": (now - self._start_time).total_seconds(),
            "phase": "EXECUTING" if self._total_calls else "LISTENING",
            "phase_detail": "Processing chat messages" if self._total_calls else "Awaiting input",
            "runtime_mode": "hybrid",
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_tokens_prompt": self._total_prompt,
            "total_tokens_completion": self._total_completion,
            "total_cost_usd": round(self._total_cost, 6),
            "last_call_at": self._last_call_at.isoformat() if self._last_call_at else None,
            "online_calls": self._mode_counts["online"],
            "offline_calls": self._mode_counts["offline"],
            "hybrid_calls": self._mode_counts["hybrid"],
            "online_tokens": self._mode_tokens["online"],
            "offline_tokens": self._mode_tokens["offline"],
            "hybrid_tokens": self._mode_tokens["hybrid"],
            "provider_stats": provider_stats,
            "tasks": telemetry_tasks,
            "recent_events": list(self._recent_events),
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

