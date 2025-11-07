import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse
from uvicorn import Config, Server
from typing import Dict
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import sqlite3
import json
from pathlib import Path
from datetime import datetime

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
        # Store references to other plugins for the dashboard
        self.all_plugins = config.get("all_plugins", {})
        self.plugin_manager = config.get("plugin_manager")
        self.event_bus = config.get("event_bus")  # Store event bus for publishing events
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

        # Dashboard endpoints
        @self.app.get("/dashboard")
        async def dashboard_ui():
            return FileResponse("frontend/dashboard.html")

        @self.app.get("/api/status")
        async def api_status():
            # Minimal runtime status for dashboard
            plugins = []
            try:
                for name, p in (self.all_plugins or {}).items():
                    plugins.append({"name": name, "class": p.__class__.__name__})
            except Exception:
                plugins = []

            return {
                "plugins": plugins,
                "connections": list(self.connections.keys()),
            }

        @self.app.get("/api/stats")
        async def api_stats():
            """Return system statistics for dashboard."""
            stats = {
                "plugin_count": 0,
                "pending_count": 0,
                "done_count": 0,
                "failed_count": 0,
            }
            
            try:
                # Count active plugins
                if self.plugin_manager and hasattr(self.plugin_manager, "plugins"):
                    stats["plugin_count"] = len(self.plugin_manager.plugins)
                elif self.all_plugins:
                    stats["plugin_count"] = len(self.all_plugins)
                
                # Count tasks by status from SQLite
                db_path = Path(".data") / "tasks.sqlite"
                if db_path.exists():
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    
                    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
                    stats["pending_count"] = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
                    stats["done_count"] = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'failed'")
                    stats["failed_count"] = cur.fetchone()[0]
                    
                    conn.close()
            except Exception as e:
                logger.error(f"Error fetching stats: {e}")
            
            return stats

        @self.app.get("/api/tasks")
        async def api_tasks(limit: int = 20):
            """Return the last `limit` tasks from the persistent SQLite queue for quick inspection."""
            db_path = Path(".data") / "tasks.sqlite"
            if not db_path.exists():
                return {"error": "tasks DB not found", "tasks": []}

            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, status, priority, payload, created_at FROM tasks ORDER BY id DESC LIMIT ?",
                    (int(limit),),
                )
                rows = cur.fetchall()
                tasks = []
                for r in rows:
                    tid, status, pr, payload, created_at = r
                    tasks.append({
                        "id": tid,
                        "status": status,
                        "priority": pr,
                        "payload": payload,
                        "created_at": created_at,
                    })
                conn.close()
                return {"tasks": tasks}
            except Exception as e:
                return {"error": str(e), "tasks": []}

        @self.app.post("/api/enqueue")
        async def api_enqueue(request: Request):
            """Enqueue a new task into the persistent queue."""
            # Parse request body
            try:
                body = await request.body()
                data = json.loads(body.decode('utf-8'))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
            
            instruction = data.get("instruction", "").strip()
            priority = data.get("priority", 100)
            
            if not instruction:
                raise HTTPException(status_code=400, detail="instruction field is required")
            
            # Insert into database
            db_path = Path(".data") / "tasks.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                
                # Ensure table exists (in case it's first run)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TEXT DEFAULT (datetime('now')),
                        priority INTEGER DEFAULT 100,
                        status TEXT DEFAULT 'pending',
                        payload TEXT
                    )
                """)
                
                payload_json = json.dumps({"instruction": instruction})
                
                cur.execute(
                    "INSERT INTO tasks (priority, status, payload, created_at) VALUES (?, 'pending', ?, ?)",
                    (int(priority), payload_json, datetime.utcnow().isoformat())
                )
                conn.commit()
                task_id = cur.lastrowid
                conn.close()
                
                logger.info(f"Task #{task_id} enqueued via WebUI: {instruction[:50]}...")
                return {"success": True, "task_id": task_id}
            except Exception as db_error:
                logger.error(f"Failed to enqueue task: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database error: {db_error}")

        @self.app.get("/api/budget")
        async def api_budget():
            """Return current budget status from cognitive_task_router plugin."""
            try:
                # Try to find the cognitive_task_router plugin
                router_plugin = None
                for name, plugin in (self.all_plugins or {}).items():
                    if name == "cognitive_task_router":
                        router_plugin = plugin
                        break
                
                if not router_plugin:
                    return {
                        "error": "Budget tracking not available (cognitive_task_router not loaded)",
                        "monthly_limit": 0,
                        "monthly_spent": 0,
                        "daily_limit": 0,
                        "daily_spent": 0,
                        "current_phase": "unknown",
                        "pacing_enabled": False
                    }
                
                # Get budget data from router plugin
                monthly_limit = getattr(router_plugin, 'monthly_limit', 30.0)
                monthly_spent = getattr(router_plugin, 'monthly_spent', 0.0)
                daily_limit = getattr(router_plugin, '_daily_limit_cache', {}).get('limit', 0.0)
                daily_spent = getattr(router_plugin, '_daily_limit_cache', {}).get('spent', 0.0)
                current_phase = getattr(router_plugin, '_current_phase', 'unknown')
                pacing_enabled = getattr(router_plugin, 'pacing_enabled', False)
                
                # Calculate percentages
                monthly_usage_pct = (monthly_spent / monthly_limit * 100) if monthly_limit > 0 else 0
                daily_usage_pct = (daily_spent / daily_limit * 100) if daily_limit > 0 else 0
                
                # Calculate days remaining in month
                from datetime import datetime
                import calendar
                now = datetime.now()
                last_day = calendar.monthrange(now.year, now.month)[1]
                days_remaining = last_day - now.day + 1
                
                return {
                    "monthly_limit": monthly_limit,
                    "monthly_spent": round(monthly_spent, 2),
                    "monthly_remaining": round(monthly_limit - monthly_spent, 2),
                    "monthly_usage_pct": round(monthly_usage_pct, 1),
                    "daily_limit": round(daily_limit, 2),
                    "daily_spent": round(daily_spent, 2),
                    "daily_remaining": round(daily_limit - daily_spent, 2),
                    "daily_usage_pct": round(daily_usage_pct, 1),
                    "current_phase": current_phase,
                    "pacing_enabled": pacing_enabled,
                    "days_remaining": days_remaining
                }
            except Exception as e:
                logger.error(f"Error fetching budget status: {e}")
                return {
                    "error": f"Failed to fetch budget: {str(e)}",
                    "monthly_limit": 0,
                    "monthly_spent": 0,
                    "daily_limit": 0,
                    "daily_spent": 0,
                    "current_phase": "error",
                    "pacing_enabled": False
                }

        @self.app.get("/api/self_improvement")
        async def api_self_improvement():
            """Return self-improvement statistics from cognitive_self_tuning and hypotheses database."""
            try:
                # Get memory_sqlite plugin
                memory_plugin = None
                for name, plugin in (self.all_plugins or {}).items():
                    if name == "memory_sqlite":
                        memory_plugin = plugin
                        break
                
                if not memory_plugin:
                    return {
                        "error": "Memory database not available",
                        "hypotheses": {},
                        "upgrade_stats": {},
                        "current_upgrade": None
                    }
                
                # Get all hypotheses
                from pathlib import Path
                import sqlite3
                
                db_path = Path(".data/memory.db")
                if not db_path.exists():
                    return {
                        "error": "Database not found",
                        "hypotheses": {},
                        "upgrade_stats": {},
                        "current_upgrade": None
                    }
                
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                
                # Count hypotheses by status
                cur.execute("""
                    SELECT status, COUNT(*) 
                    FROM hypotheses 
                    GROUP BY status
                """)
                status_counts = dict(cur.fetchall())
                
                # Get total count
                cur.execute("SELECT COUNT(*) FROM hypotheses")
                total = cur.fetchone()[0]
                
                # Get successful upgrades (deployed_validated)
                successful = status_counts.get('deployed_validated', 0)
                rolled_back = status_counts.get('deployed_rollback', 0)
                total_upgrades = successful + rolled_back
                
                # Calculate success rate
                success_rate = (successful / total_upgrades * 100) if total_upgrades > 0 else 0
                
                # Get last successful upgrade
                cur.execute("""
                    SELECT id, hypothesis_text, deployed_at, test_results
                    FROM hypotheses
                    WHERE status = 'deployed_validated'
                    ORDER BY deployed_at DESC
                    LIMIT 1
                """)
                last_upgrade_row = cur.fetchone()
                last_upgrade = None
                if last_upgrade_row:
                    import json
                    test_results = json.loads(last_upgrade_row[3]) if last_upgrade_row[3] else {}
                    last_upgrade = {
                        "hypothesis_id": last_upgrade_row[0],
                        "description": last_upgrade_row[1][:100] if last_upgrade_row[1] else "N/A",
                        "timestamp": last_upgrade_row[2] or "N/A",
                        "target_file": test_results.get("target_file", "N/A")
                    }
                
                # Get last rollback
                cur.execute("""
                    SELECT id, hypothesis_text, deployed_at, test_results
                    FROM hypotheses
                    WHERE status = 'deployed_rollback'
                    ORDER BY deployed_at DESC
                    LIMIT 1
                """)
                last_rollback_row = cur.fetchone()
                last_rollback = None
                if last_rollback_row:
                    import json
                    test_results = json.loads(last_rollback_row[3]) if last_rollback_row[3] else {}
                    last_rollback = {
                        "hypothesis_id": last_rollback_row[0],
                        "description": last_rollback_row[1][:100] if last_rollback_row[1] else "N/A",
                        "timestamp": last_rollback_row[2] or "N/A",
                        "reason": test_results.get("rollback_reason", "validation_failed")
                    }
                
                # Check for current pending upgrade
                upgrade_state_file = Path(".data/upgrade_state.json")
                current_upgrade = None
                if upgrade_state_file.exists():
                    import json
                    with open(upgrade_state_file, 'r') as f:
                        upgrade_state = json.load(f)
                    
                    current_upgrade = {
                        "in_progress": True,
                        "hypothesis_id": upgrade_state.get("hypothesis_id"),
                        "target_file": upgrade_state.get("target_file"),
                        "status": upgrade_state.get("status"),
                        "validation_attempts": upgrade_state.get("validation_attempts", 0),
                        "max_attempts": upgrade_state.get("max_attempts", 3)
                    }
                
                conn.close()
                
                return {
                    "hypotheses": {
                        "pending": status_counts.get('pending', 0),
                        "testing": status_counts.get('testing', 0),
                        "approved": status_counts.get('approved', 0),
                        "deployed_validated": successful,
                        "deployed_rollback": rolled_back,
                        "deployed_awaiting_validation": status_counts.get('deployed_awaiting_validation', 0),
                        "total": total
                    },
                    "upgrade_stats": {
                        "total_upgrades": total_upgrades,
                        "successful": successful,
                        "rolled_back": rolled_back,
                        "success_rate": round(success_rate, 1)
                    },
                    "current_upgrade": current_upgrade,
                    "last_upgrade": last_upgrade,
                    "last_rollback": last_rollback
                }
            except Exception as e:
                logger.error(f"Error fetching self-improvement stats: {e}")
                return {
                    "error": f"Failed to fetch stats: {str(e)}",
                    "hypotheses": {},
                    "upgrade_stats": {},
                    "current_upgrade": None
                }

        @self.app.get("/api/hypotheses")
        async def api_hypotheses(limit: int = 20, status: str = None):
            """Return list of hypotheses from database."""
            try:
                from pathlib import Path
                import sqlite3
                
                db_path = Path(".data/memory.db")
                if not db_path.exists():
                    return {"error": "Database not found", "hypotheses": []}
                
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                
                # Build query
                if status and status != "all":
                    query = """
                        SELECT id, hypothesis_text, category, status, priority, 
                               created_at, tested_at, approved_at, deployed_at
                        FROM hypotheses
                        WHERE status = ?
                        ORDER BY id DESC
                        LIMIT ?
                    """
                    cur.execute(query, (status, int(limit)))
                else:
                    query = """
                        SELECT id, hypothesis_text, category, status, priority,
                               created_at, tested_at, approved_at, deployed_at
                        FROM hypotheses
                        ORDER BY id DESC
                        LIMIT ?
                    """
                    cur.execute(query, (int(limit),))
                
                rows = cur.fetchall()
                hypotheses = []
                
                for row in rows:
                    hypotheses.append({
                        "id": row[0],
                        "description": row[1][:100] if row[1] else "N/A",  # Truncate
                        "category": row[2] or "unknown",
                        "status": row[3] or "pending",
                        "priority": row[4] or 100,
                        "created_at": row[5] or "N/A",
                        "tested_at": row[6] or None,
                        "approved_at": row[7] or None,
                        "deployed_at": row[8] or None
                    })
                
                conn.close()
                
                return {"hypotheses": hypotheses}
            except Exception as e:
                logger.error(f"Error fetching hypotheses: {e}")
                return {"error": f"Failed to fetch hypotheses: {str(e)}", "hypotheses": []}

        @self.app.get("/api/logs")
        async def api_logs(level: str = "ALL", lines: int = 200):
            """Return recent log entries."""
            try:
                from pathlib import Path
                import re
                
                # Find the most recent log file
                log_files = sorted(Path("logs").glob("sophia*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
                
                if not log_files:
                    return {"error": "No log files found", "logs": []}
                
                log_file = log_files[0]
                
                # Read last N lines
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                # Parse JSON log lines
                logs = []
                
                for line in recent_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Parse JSON log entry
                        log_entry = json.loads(line)
                        log_level = log_entry.get("levelname", "INFO")
                        
                        # Filter by level
                        if level != "ALL" and log_level != level:
                            continue
                        
                        logs.append({
                            "timestamp": log_entry.get("asctime", ""),
                            "level": log_level,
                            "message": f"[{log_entry.get('name', 'unknown')}] {log_entry.get('message', '')}"
                        })
                    except json.JSONDecodeError:
                        # Fallback for non-JSON lines
                        if logs:  # Append to previous message as continuation
                            logs[-1]["message"] += "\n" + line
                
                return {"logs": logs, "log_file": str(log_file)}
            except Exception as e:
                logger.error(f"Error fetching logs: {e}")
                import traceback
                traceback.print_exc()
                return {"error": f"Failed to fetch logs: {str(e)}", "logs": []}
        
        @self.app.post("/api/tools/run")
        async def run_tool(request: Request):
            """Execute a tool command."""
            try:
                data = await request.json()
                tool_name = data.get("tool")
                
                import subprocess
                import os
                
                # Map tool names to commands
                tools = {
                    "test_dashboard": ".venv/bin/python capture_dashboard_screenshots.py",
                    "test_e2e": ".venv/bin/pytest test_dashboard_e2e.py -v",
                    "test_plugins": ".venv/bin/pytest tests/ -k plugin -v",
                    "backup_db": "cp -r .data .data_backup_$(date +%Y%m%d_%H%M%S)",
                    "clear_queue": "sqlite3 .data/tasks.sqlite 'DELETE FROM tasks WHERE status=\"pending\"'",
                    "view_logs": "tail -100 logs/sophia.log",
                    "test_llama": "curl -X POST http://localhost:11434/api/generate -d '{\"model\": \"llama3.1:8b\", \"prompt\": \"test\", \"stream\": false}'",
                    "test_qwen": "curl -X POST http://localhost:11434/api/generate -d '{\"model\": \"qwen2.5:14b\", \"prompt\": \"test\", \"stream\": false}'",
                    "list_models": "curl -s http://localhost:11434/api/tags",
                    "system_info": "echo 'CPU:' && lscpu | grep 'Model name' && echo 'Memory:' && free -h",
                    "check_health": "ps aux | grep -E '(python run.py|ollama)' | grep -v grep",
                    "export_data": "curl -s http://127.0.0.1:8000/api/stats",
                    "run_diagnostics": "echo 'Disk:' && df -h . && echo 'Memory:' && free -h"
                }
                
                cmd = tools.get(tool_name)
                if not cmd:
                    return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                # Execute command
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = result.stdout or result.stderr
                success = result.returncode == 0
                
                return {
                    "success": success,
                    "message": "Command executed" if success else "Command failed",
                    "output": output[:500]  # Limit output
                }
                
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/tools/browser-test")
        async def browser_test():
            """Run browser test using cognitive_browser_control plugin."""
            try:
                # Check if browser control plugin is available
                browser_plugin = None
                
                # First try to get from all_plugins map (faster)
                if self.all_plugins:
                    browser_plugin = self.all_plugins.get("cognitive_browser_control")
                
                # Fallback: search through plugin_manager
                if not browser_plugin and self.plugin_manager:
                    for plugin_type in PluginType:
                        for plugin in self.plugin_manager.get_plugins_by_type(plugin_type):
                            if plugin.name == "cognitive_browser_control":
                                browser_plugin = plugin
                                break
                        if browser_plugin:
                            break
                
                if not browser_plugin:
                    return {
                        "success": False,
                        "error": "Browser control plugin not available - check if cognitive_browser_control is loaded"
                    }
                
                # Run dashboard test
                result = await browser_plugin.test_dashboard()
                
                return {
                    "success": result.get("success", False),
                    "total": result.get("total_tests", 0),
                    "passed": result.get("passed", 0),
                    "screenshots": result.get("screenshots", [])
                }
                
            except Exception as e:
                logger.error(f"Browser test error: {e}")
                return {"success": False, "error": str(e)}

    async def start_server(self):
        """Starts the Uvicorn server in a background task."""
        server_config = Config(self.app, host=self.host, port=self.port, log_level="info")
        server = Server(server_config)
        asyncio.create_task(server.serve())
        logger.info(f"WebUI server started at http://{self.host}:{self.port}")
        self._server_started = True

    async def execute(self, context: SharedContext) -> SharedContext:
        """Checks for user input from the WebSocket (non-blocking) and starts the server if not already running."""
        if not self._server_started:
            await self.start_server()

        # Non-blocking check for messages
        try:
            user_input, response_callback = self.input_queue.get_nowait()
            context.user_input = user_input
            context.payload["_response_callback"] = response_callback
            logger.info(f"[WebUI] Received message: {user_input}", extra={"plugin_name": "interface_webui"})
            
            # Publish USER_INPUT event to trigger processing
            if self.event_bus:
                from core.events import Event, EventType, EventPriority
                self.event_bus.publish(
                    Event(
                        event_type=EventType.USER_INPUT,
                        source="interface_webui",
                        priority=EventPriority.HIGH,
                        data={"input": user_input, "response_callback": response_callback}
                    )
                )
                logger.info(f"[WebUI] USER_INPUT event published", extra={"plugin_name": "interface_webui"})
        except asyncio.QueueEmpty:
            # No messages waiting, that's fine
            pass
            
        return context

    async def send_response(self, session_id: str, message: str):
        """Sends a message back to a specific web client."""
        if session_id in self.connections:
            await self.connections[session_id].send_text(message)
